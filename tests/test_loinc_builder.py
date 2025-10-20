import json
import os
from unittest import mock

import responses
from cumulus_library import base_utils, databases, db_config, study_manifest
from cumulus_library.apis import loinc
from cumulus_library.builders import protected_table_builder

from cumulus_library_loinc import loinc_builder


@mock.patch.dict(
    os.environ,
    clear=True,
)
@mock.patch("platformdirs.user_cache_dir")
@responses.activate
def test_static_tables(mock_dir, tmp_path):
    mock_dir.return_value = tmp_path
    responses.add(
        responses.GET,
        f"{loinc.BASE_URL}Loinc",
        match=[responses.matchers.query_param_matcher({})],
        body=json.dumps(
            {
                "version": "test",
                "downloadUrl": "http://download_url",
            }
        ),
        status=200,
    )
    with open("./tests/test_data/loinc.zip", "rb") as f:
        responses.add(
            responses.GET,
            "http://download_url",
            status=200,
            body=f.read(),
            match=[responses.matchers.request_kwargs_matcher({"stream": True})],
            headers={"Content-Length": "3656"},
        )

    db_config.db_type = "duckdb"
    db = databases.DuckDatabaseBackend(f"{tmp_path}/duckdb")
    config = base_utils.StudyConfig(
        db=db,
        loinc_user="user",
        loinc_password="password",
        schema="loinc",
    )
    db.connect()
    cursor = config.db.cursor()
    cursor.execute("CREATE SCHEMA loinc")
    manifest = study_manifest.StudyManifest(study_path="./cumulus_library_loinc/")
    p_builder = protected_table_builder.ProtectedTableBuilder()
    p_builder.execute_queries(config=config, manifest=manifest)

    builder = loinc_builder.LoincBuilder()
    builder.execute_queries(config=config, manifest=manifest)

    for table_conf in [
        {
            "name": "consumer_name",
            "size": 5,
            "first": ("93418-2", "(8;8)(q13;q21)(HEY1,NCOA2) fusion transcript analysis, Tissue"),
            "last": ("38334-9", "1,1,2-Trichloroethane, Water"),
        },
        {
            "name": "parent_group",
            "size": 5,
            "first": (
                "LG100-4",
                (
                    "Chem_DrugTox_Chal_Sero_Allergy<SAME:Comp|Prop|Tm|Syst (except intravascular "
                    "and urine)><ANYBldSerPlas,ANYUrineUrineSed><ROLLUP:Method>"
                ),
                "ACTIVE",
            ),
            "last": ("LG27-5", "CellDiffCount<SAME:Comp|Prop|Tm|Sys><ROLLUP:Meth>", "ACTIVE"),
        },
        {
            "name": "parent_group_attributes",
            "size": 5,
            "first": (
                "LG100-4",
                "Description",
                (
                    "This parent group contains groups for terms in any of the following classes: "
                    "CHEM, DRUG/TOX, CHAL, SERO, and ALLERGY. Each group contains terms with the "
                    "same Component, Property, and Time aspect. The terms in a given group also "
                    "have the same System, except when the System is in the intravascular or "
                    "urine category, in which case terms that have any of the Systems in that "
                    "category are rolled up. For example, a group for a given analyte in CSF "
                    "only has terms with the System 'CSF', but a group for an analyte in an "
                    "intravascular specimen contains terms with a variety of Systems, "
                    "including 'Bld', 'Ser/Plas', 'BldV', etc. Some intravascular Systems are "
                    "purposely excluded from this rollup, including cord blood ('BldCo') and "
                    "dried blood spots (DBS)."
                ),
            ),
            "last": (
                "LG27-5",
                "Description",
                (
                    "This parent group contains specific groups for each type of cell in a cell "
                    "differential. Each individual group contains terms with the same cell type, "
                    "Property (e.g., number concentration), Time aspect, and System, regardless "
                    "of the Method. These groups mostly combine methodless terms with those that "
                    "specify automated or manual counts."
                ),
            ),
        },
        {
            "name": "group_loinc_terms",
            "size": 5,
            "first": (
                None,
                "LG51973-2",
                None,
                "100675-8",
                (
                    "Cytomegalovirus DNA [Units/volume] (viral load) in Blood by NAA with "
                    "probe detection"
                ),
            ),
            "last": (
                None,
                "LG51973-2",
                None,
                "72493-0",
                (
                    "Cytomegalovirus DNA [Units/volume] (viral load) in Serum or Plasma "
                    "by NAA with probe detection"
                ),
            ),
        },
        {
            "name": "group_attributes",
            "size": 5,
            "first": ("LG100-4", "LG10324-8", "MolecularWeightOfAnalyte", 176.219),
            "last": ("LG100-4", "LG10852-8", "MolecularWeightOfAnalyte", 94.97),
        },
        {
            "name": "group",
            "size": 5,
            "first": (
                "LG100-4",
                "LG8749-6",
                (
                    "(Acer negundo+Betula verrucosa+Fagus grandifolia+Quercus alba+Juglans "
                    "californica) Ab.IgE|ACnc|Pt|ANYBldSerPl"
                ),
                None,
                "Active",
                None,
            ),
            "last": (
                "LG100-4",
                "LG8717-3",
                (
                    "(Alnus incana+Corylus avellana+Ulmus americana+Salix caprea+Populus "
                    "deltoides) Ab.IgE|ACnc|Pt|ANYBldSerPl"
                ),
                None,
                "Active",
                None,
            ),
        },
        {
            "name": "document_ontology",
            "size": 5,
            "first": ("100018-1", "LP173418-7", "Document.Kind", 1, "Note"),
            "last": ("100438-1", "LP173213-2", "Document.TypeOfService", 1, "Progress"),
        },
        {
            "name": "lab_orders",
            "size": 5,
            "first": ("42176-8", "1,3 beta glucan [Mass/volume] in Serum", "Both"),
            "last": ("1668-3", "17-Hydroxyprogesterone [Mass/volume] in Serum or Plasma", "Both"),
        },
        {
            "name": "loinc_core",
            "size": 5,
            "first": (
                "100000-9",
                "Health informatics pioneer and the father of LOINC",
                "Hx",
                "Pt",
                "^Patient",
                "Nar",
                None,
                "H&P.HX",
                2,
                "Health informatics pioneer and the father of LOINC",
                "Health Info Pioneer+Father of LOINC",
                None,
                "ACTIVE",
                2.74,
                2.74,
            ),
            "last": (
                "100004-1",
                "Demonstrates knowledge of the expected psychosocial responses to the procedure",
                "Find",
                "Pt",
                "^Patient",
                "Ord",
                None,
                "SURVEY.PNDS",
                4,
                "Demonstrates knowledge of the expected psychosocial responses to the procedure",
                None,
                None,
                "ACTIVE",
                2.72,
                2.72,
            ),
        },
        {
            "name": "map_to",
            "size": 5,
            "first": ("1009-0", "1007-4", None),
            "last": ("101764-9", "101765-6", None),
        },
    ]:
        res = cursor.execute(f'SELECT * from "loinc"."{table_conf["name"]}"').fetchall()
        assert len(res) == table_conf["size"]
        assert res[0] == table_conf["first"]
        assert res[-1] == table_conf["last"]
