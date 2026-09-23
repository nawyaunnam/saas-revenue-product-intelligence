{% macro month_start(col) %}cast(date_trunc('month', {{ col }}) as date){% endmacro %}
{% macro add_days(col, n) %}
  {% if target.type == 'snowflake' %} dateadd(day, {{ n }}, {{ col }})
  {% else %} ({{ col }} + interval '{{ n }} days') {% endif %}
{% endmacro %}
{% macro month_diff(a, b) %}datediff('month', {{ a }}, {{ b }}){% endmacro %}
{% macro day_diff(a, b) %}datediff('day', {{ a }}, {{ b }}){% endmacro %}
