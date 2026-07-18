from flask import Blueprint

genes_bp = Blueprint(
    "genes",
    __name__,
    url_prefix="/genes",
    template_folder="../../templates/genes"
)

from . import routes