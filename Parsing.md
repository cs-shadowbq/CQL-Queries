# Parsing

The main difference between writing a parser and writing a CQL search query is that you cannot use aggregate functions:
* `groupBy()`
* `table()`
* `worldMap()`

## creating tagged fields

Dont add a # to a field, go into "Parser > Settings> Fields" to Tag and add `myFieldName` to the list if you intend to tag the field. The parser script will now produce a field named `#myFieldName` and remove `myFieldName` from the event.