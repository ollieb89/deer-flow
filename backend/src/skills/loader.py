import os
from pathlib import Path

from .parser import parse_skill_file
from .types import Skill


def get_skills_root_path() -> Path:
    """
    Get the root path of the skills directory.

    Returns:
        Path to the skills directory (deer-flow/skills)
    """
    # backend directory is current file's parent's parent's parent
    backend_dir = Path(__file__).resolve().parent.parent.parent
    # skills directory is sibling to backend directory
    skills_dir = backend_dir.parent / "skills"
    return skills_dir


def load_skills(
    skills_path: Path | None = None, use_config: bool = True, enabled_only: bool = False, agent_name: str | None = None
) -> list[Skill]:
    """
    Load all skills from the skills directory.

    Scans public, custom, and optionally agent-local skill directories, parsing
    SKILL.md files to extract metadata. The enabled state is determined by the
    skills_state_config.json file for public/custom skills, while agent-local
    skills are enabled by default.

    Args:
        skills_path: Optional custom path to skills directory.
                     If not provided and use_config is True, uses path from config.
                     Otherwise defaults to deer-flow/skills
        use_config: Whether to load skills path from config (default: True)
        enabled_only: If True, only return enabled skills (default: False)
        agent_name: Optional name of the agent to load local skills for.

    Returns:
        List of Skill objects, sorted by name
    """
    if skills_path is None:
        if use_config:
            try:
                from src.config import get_app_config

                config = get_app_config()
                skills_path = config.skills.get_skills_path()
            except Exception:
                # Fallback to default if config fails
                skills_path = get_skills_root_path()
        else:
            skills_path = get_skills_root_path()

    skills = []

    # 1. Scan public and custom directories
    if skills_path.exists():
        for category in ["public", "custom"]:
            category_path = skills_path / category
            if not category_path.exists() or not category_path.is_dir():
                continue

            for current_root, dir_names, file_names in os.walk(category_path):
                # Keep traversal deterministic and skip hidden directories.
                dir_names[:] = sorted(name for name in dir_names if not name.startswith("."))
                if "SKILL.md" not in file_names:
                    continue

                skill_file = Path(current_root) / "SKILL.md"
                relative_path = skill_file.parent.relative_to(category_path)

                skill = parse_skill_file(skill_file, category=category, relative_path=relative_path)
                if skill:
                    skills.append(skill)

    # 2. Scan agent-specific skills if agent_name provided
    if agent_name:
        try:
            from src.config.paths import get_paths

            agent_skills_path = get_paths().agent_skills_dir(agent_name)
            if agent_skills_path.exists() and agent_skills_path.is_dir():
                for current_root, dir_names, file_names in os.walk(agent_skills_path):
                    dir_names[:] = sorted(name for name in dir_names if not name.startswith("."))
                    if "SKILL.md" not in file_names:
                        continue

                    skill_file = Path(current_root) / "SKILL.md"
                    relative_path = skill_file.parent.relative_to(agent_skills_path)

                    skill = parse_skill_file(skill_file, category="agent", relative_path=relative_path)
                    if skill:
                        # Agent-local skills are enabled by default
                        skill.enabled = True
                        skills.append(skill)
        except Exception as e:
            print(f"Warning: Failed to load agent-local skills for {agent_name}: {e}")

    # Load skills state configuration and update enabled status for public/custom skills
    try:
        from src.config.extensions_config import ExtensionsConfig

        extensions_config = ExtensionsConfig.from_file()
        for skill in skills:
            # We only manage enabled status via config for public and custom skills.
            # Agent skills are already set to True by default above.
            if skill.category in ["public", "custom"]:
                skill.enabled = extensions_config.is_skill_enabled(skill.name, skill.category)
    except Exception as e:
        # If config loading fails, default to all enabled (except agent skills which are already True)
        print(f"Warning: Failed to load extensions config: {e}")
        for skill in skills:
            if skill.category in ["public", "custom"]:
                skill.enabled = True

    # Filter by enabled status if requested
    if enabled_only:
        skills = [skill for skill in skills if skill.enabled]

    # Sort by name for consistent ordering
    skills.sort(key=lambda s: s.name)

    return skills
