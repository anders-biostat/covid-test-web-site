Extract Messages:

```
pybabel extract -F babel.cfg -k _l -o messages.pot .
```

Update Messages:

```
pybabel update -i messages.pot -d ../translations
```

Compile Messages:

```
pybabel compile -d ../translations            
```

Init new language catalog (example: de):

```
pybabel init -i messages.pot -d translations -l de
```