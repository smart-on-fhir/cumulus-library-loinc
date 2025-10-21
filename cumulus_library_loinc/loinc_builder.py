import re

import pandas
from cumulus_library import BaseTableBuilder, base_utils, log_utils, study_manifest
from cumulus_library.apis import loinc
from cumulus_library.template_sql import base_templates

# Loinc has a bunch of tables we don't need, so we specify the ones we'd like to
# create tables from in this list
LOINC_TABLE_SUBSET = [
    # Consumer names for medications
    ("consumer_name", "AccessoryFiles/ConsumerName/ConsumerName.csv"),
    # Hierarchichal grouping
    ("parent_group", "AccessoryFiles/GroupFile/ParentGroup.csv"),
    ("parent_group_attributes", "AccessoryFiles/GroupFile/ParentGroupAttributes.csv"),
    ("group_loinc_terms", "AccessoryFiles/GroupFile/GroupLoincTerms.csv"),
    ("group_attributes", "AccessoryFiles/GroupFile/GroupAttributes.csv"),
    ("group", "AccessoryFiles/GroupFile/Group.csv"),
    # documents
    ("document_ontology", "AccessoryFiles/DocumentOntology/DocumentOntology.csv"),
    # Lab orders
    (
        "lab_orders",
        "AccessoryFiles/LoincUniversalLabOrdersValueSet/LoincUniversalLabOrdersValueSet.csv",
    ),
    # Primary value set
    ("loinc_core", "LoincTableCore/LoincTableCore.csv"),
    # Obselete term mapping
    ("map_to", "LoincTableCore/MapTo.csv"),
]


class LoincBuilder(BaseTableBuilder):
    def get_loinc_data(
        self,
        user: str,
        password: str,
        force_upload: bool,
    ):
        api = loinc.LoincApi(user=user, password=password)
        new = False
        version, url = api.get_download_info()
        api.download_loinc_dataset(version=version, download_url=url)
        return version, new, api

    def snake_case(self, x: str) -> str:
        """Converts either CAPS_CASE or CamelCase to snake_case"""
        return re.sub(r"([a-z])([A-Z])", r"\1_\2", x).lower()

    def prepare_queries(
        self,
        config: base_utils.StudyConfig,
        manifest: study_manifest.StudyManifest,
        *args,
        **kwargs,
    ):
        loinc_version, new_version, api = self.get_loinc_data(
            config.loinc_user, config.loinc_password, config.force_upload
        )
        parquet_path = api.cache_dir / f"generated_parquet/{loinc_version}"

        with base_utils.get_progress_bar() as progress:
            task = progress.add_task(
                None,
                total=len(LOINC_TABLE_SUBSET),
            )
            for table in LOINC_TABLE_SUBSET:
                progress.update(task, description=f"Compressing {table[1]}...")
                # The loinc core table has some nulls that break type inference,
                # and since these tables are relatively small, we'll override the
                # chunking behavior and read them all in at once.
                df = pandas.read_csv(
                    api.download_dir / f"{loinc_version}/{table[1]}", low_memory=False
                )
                df = df.rename(self.snake_case, axis="columns")
                file_path = parquet_path / table[1].replace(".csv", ".parquet")
                file_path.parent.mkdir(exist_ok=True, parents=True)
                df.to_parquet(file_path)
                progress.update(task, description=f"Uploading {file_path.name}...")
                remote_path = config.db.upload_file(
                    file=file_path,
                    study=manifest.get_study_prefix(),
                    topic=file_path.stem,
                    force_upload=config.force_upload or new_version or True,
                )
                self.queries.append(
                    base_templates.get_ctas_from_parquet_query(
                        schema_name=config.schema,
                        table_name=table[0],
                        local_location=file_path,
                        remote_location=remote_path,
                        table_cols=df.columns,
                        remote_table_cols_types=["STRING" for x in df.columns],
                    )
                )
                progress.advance(task)
        log_utils.log_transaction(
            config=config, manifest=manifest, message=f"Loinc version: {loinc_version}"
        )
