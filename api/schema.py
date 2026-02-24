from drf_spectacular.openapi import AutoSchema


class TaggedAutoSchema(AutoSchema):
    """Use view.schema_tags for grouping endpoints in the schema."""

    def get_tags(self):
        view = self.view
        tags = getattr(view, 'schema_tags', None)
        if tags:
            return tags
        return super().get_tags()
