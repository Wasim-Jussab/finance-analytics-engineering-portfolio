{% macro checkpoint_duckdb() %}
    {% if target.type == 'duckdb' %}
        {% do run_query('force checkpoint') %}
    {% endif %}
{% endmacro %}
