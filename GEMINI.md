# Project Rules: NeptunSmart

## Release on Approval
Когда пользователь утверждает предложенные правки (например, пишет "утверждаю", "применяем", "выпусти патч", "сделай релиз", "сохраняй" и т.п.):
1. Активируйте скилл `auto-release` (`.agents/skills/auto-release/SKILL.md`).
2. Повысьте версию (patch или minor) в `custom_components/neptun_smart_local/manifest.json`.
3. Убедитесь в наличии корректного `hacs.json` в корне.
4. Закоммитьте изменения, создайте тег `vX.Y.Z` и отправьте изменения в GitHub.
5. Автоматически создайте GitHub Release с описанием изменений через `/opt/homebrew/bin/gh release create`.
