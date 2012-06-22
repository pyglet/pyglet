`{{ objname }}` Class
==============================================================

.. template class.rst

.. currentmodule:: {{ module }}

.. inheritance-diagram:: {{ objname }}

.. autoclass:: {{ objname }}

{% block events %}
{% if events %}

Events
------

.. autosummary::
{% for item in events %}
   ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block methods %}
{% if methods %}

Methods
-------

.. autosummary::
{% for item in methods %}
   ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block attributes %}
{% if attributes %}
   
Attributes
----------

.. autosummary::
{% for item in attributes %}
   ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

..

.. rubric:: Descriptions

.. class:: {{ objname }}


{% block events_desc %}
{% if def_events %}

   .. rubric:: Event details

{% for item in def_events %}

   .. automethod:: {{ item }}

{%- endfor %}
{% endif %}
{% endblock %}

{% block methods_desc %}
{% if def_methods %}

   .. rubric:: Method details

{% for item in def_methods %}

   .. automethod:: {{ item }}

{%- endfor %}
{% endif %}
{% endblock %}

{% block attributes_desc %}
{% if def_attributes %}

   .. rubric:: Attribute details

{% for item in def_attributes %}

   .. autoattribute:: {{ item }}

{%- endfor %}
{% endif %}
{% endblock %}





{% if inherited %}

   .. rubric:: Inherited member details

{% block inh_events_desc %}
{% if inh_events %}
{% for item in inh_events %}

   .. automethod:: {{ item }}
      :noindex:

{%- endfor %}
{% endif %}
{% endblock %}

{% block inh_methods_desc %}
{% if inh_methods %}
{% for item in inh_methods %}

   .. automethod:: {{ item }}
      :noindex:

{%- endfor %}
{% endif %}
{% endblock %}

{% block inh_attributes_desc %}
{% if inh_attributes %}
{% for item in inh_attributes %}

   .. autoattribute:: {{ item }}
      :noindex:

{%- endfor %}
{% endif %}
{% endblock %}

{% endif %}

