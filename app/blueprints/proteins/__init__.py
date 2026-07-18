from flask import Blueprint

proteins_bp = Blueprint(
    "proteins",
    __name__,
    url_prefix="/proteins",
    template_folder="../../templates/proteins"
)

from . import routes