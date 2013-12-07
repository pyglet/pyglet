{{ fullname }}
===========================================================

.. automodule:: {{ fullname }}


{% block submodules %}
{% if submodules %}

Modules
-------

.. autosummary::
   :toctree: {{ objname  }}/
   :template: module.rst

{% for item in submodules %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}


{% block classes %}
{% if classes %}

Classes
-------

.. autosummary::
   :nosignatures:
   :toctree: {{ objname  }}/
   :template: class.rst

{% for item in classes %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block functions %}
{% if functions %}

Functions
---------
   
.. autosummary::
   :toctree: {{ objname  }}/

{% for item in functions %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}


{% block exceptions %}
{% if exceptions %}

Exceptions
----------

.. autosummary::
   :toctree: {{ objname  }}/
   :template: exception.rst

{% for item in exceptions %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}


.. template package.rst
