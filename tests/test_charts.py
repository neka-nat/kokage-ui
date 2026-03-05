"""Tests for Chart component."""

from kokage_ui.charts import Chart


class TestChart:
    def test_renders_canvas(self):
        c = Chart(type="bar", data={"labels": ["A"], "datasets": []})
        result = str(c)
        assert "<canvas" in result
        assert "</canvas>" in result

    def test_renders_script(self):
        c = Chart(type="bar", data={"labels": ["A"], "datasets": []})
        result = str(c)
        assert "<script>" in result
        assert "new Chart(" in result

    def test_chart_type_in_config(self):
        c = Chart(type="pie", data={"labels": [], "datasets": []})
        result = str(c)
        assert '"type": "pie"' in result

    def test_data_serialized(self):
        data = {"labels": ["Jan", "Feb"], "datasets": [{"label": "Sales", "data": [10, 20]}]}
        c = Chart(type="bar", data=data)
        result = str(c)
        assert '"Jan"' in result
        assert '"Feb"' in result

    def test_custom_chart_id(self):
        c = Chart(type="bar", data={"labels": [], "datasets": []}, chart_id="my-chart")
        result = str(c)
        assert 'id="my-chart"' in result

    def test_auto_generated_id(self):
        c = Chart(type="bar", data={"labels": [], "datasets": []})
        result = str(c)
        assert "kokage-chart-" in result

    def test_dimensions(self):
        c = Chart(type="bar", data={"labels": [], "datasets": []}, width="50%", height="300px")
        result = str(c)
        assert "width:50%" in result
        assert "height:300px" in result

    def test_default_dimensions(self):
        c = Chart(type="bar", data={"labels": [], "datasets": []})
        result = str(c)
        assert "width:100%" in result
        assert "height:400px" in result

    def test_responsive_default(self):
        c = Chart(type="bar", data={"labels": [], "datasets": []})
        result = str(c)
        assert '"responsive": true' in result

    def test_responsive_false(self):
        c = Chart(type="bar", data={"labels": [], "datasets": []}, responsive=False)
        result = str(c)
        assert '"responsive": true' not in result

    def test_options_passed(self):
        c = Chart(
            type="bar",
            data={"labels": [], "datasets": []},
            options={"plugins": {"legend": {"position": "top"}}},
        )
        result = str(c)
        assert '"legend"' in result
        assert '"position"' in result

    def test_destroys_existing_chart(self):
        c = Chart(type="bar", data={"labels": [], "datasets": []})
        result = str(c)
        assert "Chart.getChart" in result
        assert ".destroy()" in result

    def test_iife_wrapper(self):
        c = Chart(type="bar", data={"labels": [], "datasets": []})
        result = str(c)
        assert "(function(){" in result
        assert "})()" in result
