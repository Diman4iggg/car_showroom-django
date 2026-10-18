# Изображения диаграмм

Документация использует PNG, которые отображаются обычным Markdown-просмотрщиком без поддержки Mermaid. Файлы `.mmd` содержат редактируемые исходники.

| Исходник и изображение | Назначение |
|---|---|
| `architecture.mmd` / `architecture.png` | Компоненты системы |
| `deployment.mmd` / `deployment.png` | Развёртывание |
| `use-case-client.mmd` / `use-case-client.png` | Варианты использования гостя и клиента |
| `use-case-staff.mmd` / `use-case-staff.png` | Варианты использования сотрудника и администратора |
| `order-states-overview.mmd` / `order-states-overview.png` | Состояния заказа в спецификации |
| `order-states.mmd` / `order-states.png` | Состояния заказа в отдельном документе |
| `models.mmd` / `models.png` | Диаграмма моделей |

Для повторной генерации нужен Node.js с доступным модулем `playwright` и установленный Chrome. Из корня проекта:

```powershell
node tools/render_diagrams.cjs
```

Для одной схемы:

```powershell
node tools/render_diagrams.cjs order-states.mmd
```

Если установлен Edge вместо Chrome, задайте `$env:DIAGRAM_BROWSER="msedge"`. Если Playwright находится вне проекта, его каталог модулей можно передать через `NODE_PATH`. При генерации библиотека Mermaid 11.4.1 загружается из CDN; для просмотра готовых PNG интернет не нужен.
