# Utils package
from utils.helpers import (
    generate_unique_id,
    get_file_extension,
    format_timestamp,
    ensure_directory_exists,
    chunk_list,
    flatten_dict
)
from utils.case_path_resolver import CasePathResolver
from utils.ui_components import show_active_case_indicator 