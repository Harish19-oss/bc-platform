from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import admin_bp
from app.models.admin import AdminUser

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password')
    return render_template('admin/login.html')


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    from app.models.gene import Gene
    from app.models.mutation import Mutation
    from app.models.pathway import Pathway
    from app.models.drug import Drug
    from app.models.publication import Publication
    from app.models.subtype import Subtype
    from app.models.protein import Protein

    return render_template("admin/dashboard.html",
        gene_count=Gene.query.count(),
        mutation_count=Mutation.query.count(),
        pathway_count=Pathway.query.count(),
        drug_count=Drug.query.count(),
        pub_count=Publication.query.count(),
        subtype_count=Subtype.query.count(),
        protein_count=Protein.query.count()
    )


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))