"""Django templates have no native slot/children mechanism. ``capture``
renders a block and stores it in a context variable instead of printing
it inline — the only way to fill a component's ``body_slot``/
``action_slot`` parameter (Modal, Drawer, EmptyState — tech.md §8).
"""

from __future__ import annotations

from django import template
from django.utils.safestring import SafeString, mark_safe

register = template.Library()


class CaptureNode(template.Node):
    def __init__(self, nodelist: template.NodeList, target_var: str) -> None:
        self.nodelist = nodelist
        self.target_var = target_var

    def render(self, context: template.Context) -> str:
        # Safe because this re-marks a block this same template engine just
        # rendered (autoescaping already applied to every variable inside
        # it) — capturing it as safe is what makes {% capture %} usable at
        # all as a slot mechanism, not a raw-string bypass of escaping.
        output: SafeString = mark_safe(self.nodelist.render(context))  # noqa: S308 # nosec
        context[self.target_var] = output
        return ""


@register.tag(name="capture")
def do_capture(parser: template.base.Parser, token: template.base.Token) -> CaptureNode:
    """``{% capture as varname %}...{% endcapture %}``"""
    bits = token.split_contents()
    if len(bits) != 3 or bits[1] != "as":
        raise template.TemplateSyntaxError("usage: {% capture as varname %}...{% endcapture %}")
    target_var = bits[2]
    nodelist = parser.parse(("endcapture",))
    parser.delete_first_token()
    return CaptureNode(nodelist, target_var)
