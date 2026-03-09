# DeerFlow Unified Memory - HOT Tier

> Keep ≤100 lines. Most-used patterns and confirmed preferences live here.
> Auto-promoted from corrections when used 3x in 7 days.
> Demoted to WARM after 30 days of inactivity.

## Global Preferences

- Format: ISO 8601 for all dates/times
- Communication: Direct, no fluff, include citations when available
- Code quality: TDD compliance, proper error handling, documentation
- Default stack: TypeScript strict mode, pnpm, conventional commits

## Project Patterns (DeerFlow)

- Always check existing `.learnings/` before creating new fixes
- Use `using-superpowers` skill for disciplined task execution
- Maintain CLAUDE.md and AGENTS.md sync with learnings
- Follow deer-flow development workflow and TDD

## Domain Patterns

### Code Generation
- Prefer explicit over implicit types
- Add error boundaries and fail-fast checks
- Include unit tests with >80% coverage
- Use mocks/stubs for external dependencies

### Documentation
- Keep README.md updated with setup instructions
- Document API contracts with OpenAPI/Swagger
- Include examples in code comments
- Generate changelog from commit history

### Testing
- Arrange-Act-Assert pattern with clear descriptions
- Edge cases: null, undefined, empty, boundary values
- Integration tests for critical paths
- Performance tests for high-traffic endpoints

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pnpm run test` | Run test suite |
| `pnpm run build` | Production build |
| `pnpm run dev` | Development server |
| `git log --oneline --graph` | Visual history |

---