from pydantic import BaseModel
from pydantic import ConfigDict

from app.core.constants import PlayingStyle
from app.core.constants import SkillLevel
from app.schemas.common import BudgetRangeInput
from app.schemas.common import PriorityValue
from app.schemas.common import TensionValue


class ProfilePayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    skill_level: SkillLevel | None = None
    playing_style: PlayingStyle | None = None
    budget: BudgetRangeInput | None = None
    preferred_tension: TensionValue | None = None
    durability_priority: PriorityValue | None = None
    repulsion_priority: PriorityValue | None = None
    control_priority: PriorityValue | None = None
    sound_priority: PriorityValue | None = None
    tension_retention_priority: PriorityValue | None = None
