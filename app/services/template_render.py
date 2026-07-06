def render_template(template, variables):
    subject = template.subject.format_map(_SafeDict(variables))
    body = template.body.format_map(_SafeDict(variables))
    return subject, body


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"
