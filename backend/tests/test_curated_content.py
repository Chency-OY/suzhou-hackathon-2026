import json
from pathlib import Path

from app.models import DoctorPersona, Scenario, TrainingProgram
from app.personas.validate import validate_persona
from app.scenarios.generate import ScenarioDraft, check_draft


def test_published_courses_have_valid_synthetic_content():
    programs = [TrainingProgram.model_validate(x) for x in json.loads(Path("data/programs.json").read_text())]
    program_ids = {program.id for program in programs}
    personas = [DoctorPersona.model_validate_json(x) for x in
                Path("data/personas/personas.jsonl").read_text().splitlines() if x.strip()]
    scenarios = [Scenario.model_validate_json(x) for x in
                 Path("data/scenarios/scenarios.jsonl").read_text().splitlines() if x.strip()]
    by_id = {persona.id: persona for persona in personas}

    assert program_ids == {"general", "xinermei"}
    assert len(by_id) == len(personas) >= 10
    assert len({scenario.id for scenario in scenarios}) == len(scenarios) >= 16
    assert {scenario.program_id for scenario in scenarios} == program_ids
    assert all(not validate_persona(persona) for persona in personas)

    for scenario in scenarios:
        assert scenario.persona_id in by_id
        draft = ScenarioDraft(**scenario.model_dump(
            include={"rep_goal", "context_brief", "opening_line", "success_criteria"}))
        assert check_draft(by_id[scenario.persona_id], draft) is None, scenario.id
        if scenario.program_id == "general":
            public_text = scenario.rep_goal + scenario.context_brief + scenario.opening_line
            assert not any(name in public_text for name in ("信尔美", "玛仕度肽", "司美格鲁肽", "替尔泊肽"))
