import json
import shutil
import os
from sotd.enrich.run import _process_month


# def test_enrich_e2e(tmp_path):
#     os.chdir(tmp_path)  # 👈 change to use the isolated test dir
#     # Prepare fake input path
#     input_dir = tmp_path / "data" / "extracted"
#     input_dir.mkdir(parents=True)
#     input_file = input_dir / "2025-04.json"

#     input_data = {
#         "metadata": {},
#         "data": [
#             {"id": "abc123", "blade": "Feather (4)", "brush": "Omega Boar 26mm"},
#             {"id": "def456", "blade": "Derby Extra", "brush": "Shore Shave"},
#         ],
#     }

#     with input_file.open("w", encoding="utf-8") as f:
#         json.dump(input_data, f)

#     # Output dir
#     output_dir = tmp_path / "data" / "enriched"
#     output_dir.mkdir(parents=True)

#     # Run enrichment
#     _process_month(2025, 4, str(output_dir), force=True, debug=False)

#     # Validate output
#     output_file = output_dir / "2025-04.json"
#     assert output_file.exists()

#     with output_file.open("r", encoding="utf-8") as f:
#         result = json.load(f)

#     assert "metadata" in result
#     assert result["metadata"]["total_records"] == 2
#     assert result["metadata"]["blade_enriched"] == 1
#     assert result["metadata"]["brush_enriched"] == 1

#     enriched = result["data"]
#     assert enriched[0]["blade"] == "Feather"
#     assert enriched[0]["blade_use"] == 4
#     assert enriched[0]["brush_fiber"] == "Boar"
#     assert enriched[0]["brush_knot_mm"] == 26
