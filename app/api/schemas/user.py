from marshmallow import fields, validate, validates_schema, ValidationError, validates, pre_load, Schema

from app.extensions import ma
from app.api.models.user import UserModel, RoleModel


class RolesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserModel
        load_instance = True


class UserSchema(ma.SQLAlchemyAutoSchema):

    email = fields.String(
        validate=[
            validate.Email(), 
        ],
        required=True
    )

    name = fields.String(required=True)

    password = fields.String(
        validate=[
            validate.Length(min=3),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error="password must only contain letters, numbers and underscores."),
        ],
        required=True
    )

    def transform_to_lower(self, data, field_name):
        if field_name in data:
            data[field_name] = data[field_name].lower()
        return data

    @pre_load
    def transform_fields(self, data, **kwargs):
        self.transform_to_lower(data, "email")
        return data

    @validates("email")
    def validate_email(self, email):
        user_id = self.context.get('user_id')
        if email:
            query = UserModel.query.filter(UserModel.email == email)
            if user_id:
                query = query.filter(UserModel.id != user_id)
            if query.first():
                raise ValidationError('this email already exists')

    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True


class UserUpdateRolesSchema(ma.SQLAlchemyAutoSchema):

    @validates("roles")
    def validate_roles(self, roles):
        if not roles:
            return roles

        role_ids = [role.id for role in RoleModel.query.all()]

        for role in roles:
            if role.id not in role_ids:
                raise ValidationError(f"Role ID {role.id} does not exist")
        
        return roles

    @validates("is_admin")
    def validate_is_admin(self, is_admin):
        users_admin = UserModel.query.filter(UserModel.is_admin == True).count()
        if users_admin == 1 and is_admin == False:
            raise ValidationError("The system needs at least one admin user")
        
        return is_admin

    class Meta:
        model = UserModel
        load_instance = True
        include_relationships = True


class UserUpdatePasswordSchema(Schema):

    old_password = fields.String(
        error_messages={"required": "Field 'old_password' is required."},
    )

    new_password = fields.String(
        validate=[
            validate.Length(min=3),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error="new_password must only contain letters, numbers and underscores."),
        ],
        error_messages={"required": "Field 'new_password' is required."},
    )
