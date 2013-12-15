`{{ objname }}` Class
==============================================================

.. template class.rst

.. currentmodule:: {{ module }}

.. inheritance-diagram:: {{ objname }}

.. autoclass:: {{ objname }}
  

{% block constructor_desc %}
{% if constructor %}

   **Constructor:**

   .. automethod:: {{ objname }}.__init__


{% endif %}
{% endblock %}


{% block methods %}
{% if methods %}

   **Methods:**

      .. autosummary::
{% for item in methods %}
         ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}


{% block events %}
{% if events %}

   **Events:**

      .. autosummary::
{% for item in events %}
         ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}


{% block attributes %}
{% if attributes %}
   
   **Attributes:**

      .. autosummary::
{% for item in attributes %}
         ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}



{% block methods_desc %}
{% if def_methods %}

Methods
-------

{% for item in def_methods %}

.. automethod:: {{ objname }}.{{ item }}

{%- endfor %}
{% endif %}
{% endblock %}



{% block events_desc %}
{% if def_events %}

Events
------

{% for item in def_events %}

.. automethod:: {{ objname }}.{{ item }}

{%- endfor %}
{% endif %}
{% endblock %}


{% block attributes_desc %}
{% if def_attributes %}

Attributes
----------

{% for item in def_attributes %}

.. autoattribute:: {{ objname }}.{{ item }}

{%- endfor %}
{% endif %}
{% endblock %}

{% block iattributes_desc %}
{% if iattributes %}

Instance Attributes
-------------------

{% for item in iattributes %}

.. attribute:: {{ objname }}.{{ item.name }}

   {{ item.doc }}

{%- endfor %}
{% endif %}
{% endblock %}

{% if inherited %}

Inherited members
-----------------


{% block inh_methods_desc %}
{% if inh_methods %}

   .. rubric:: Methods

{% for item in inh_methods %}

   .. automethod:: {{ objname }}.{{ item }}
      :noindex:

{%- endfor %}
{% endif %}
{% endblock %}


{% block inh_events_desc %}
{% if inh_events %}

   .. rubric:: Events

{% for item in inh_events %}

   .. automethod:: {{ objname }}.{{ item }}
      :noindex:

{%- endfor %}
{% endif %}
{% endblock %}


{% block inh_attributes_desc %}
{% if inh_attributes %}

   .. rubric:: Attributes

{% for item in inh_attributes %}

   .. autoattribute:: {{ objname }}.{{ item }}
      :noindex:

{%- endfor %}
{% endif %}
{% endblock %}

{% endif %}

