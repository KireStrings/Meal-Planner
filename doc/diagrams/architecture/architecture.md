```mermaid
architecture-beta
    group mealano[Mealano]
    service db(database)[Database] in mealano
    service backend(server)[Backend] in mealano
    service frontend(internet)[Frontend] in mealano
    db:R -- L:backend
    backend:R -- L:frontend

    group spoonacular[Spoonacular]
    service api(cloud)[API] in spoonacular
    service db_s(database)[Database] in spoonacular
    db_s:R -- L:api

    backend:T -- B:api
```