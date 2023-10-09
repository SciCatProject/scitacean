{{ fullname | escape | underline }}

{% set constructors = {"Client": ["from_credentials", "from_token", "without_login"],
                       "Dataset": ["__init__", "from_download_models"],
                       "File": ["from_local", "from_remote", "from_download_model"],
                       "OrigDatablockProxy": ["__init__", "from_download_model"],
                       "PID": ["__init__", "parse"],
                       "ScicatClient": ["from_credentials", "from_token", "without_login"],
                       "Thumbnail": ["__init__", "load_file", "parse"],
                      } %}
{% set regular_methods = methods | reject("in", constructors.get(name, []) + ["__init__"]) | list %}


.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :members:

   {% block methods %}
   .. rubric:: {{ _('Constructors') }}

   .. autosummary::
   {% for item in constructors[name] or ["__init__"] %}
      ~{{ name }}.{{ item }}
   {%- endfor %}

   {% if regular_methods -%}
   .. rubric:: {{ _('Methods') }}

   .. autosummary::
   {% for item in regular_methods %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {%- endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {% for item in attributes %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% if not constructors[name] or "__init__" in constructors[name] -%}
   .. automethod:: __init__
   {%- endif %}
