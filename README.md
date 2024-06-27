# Report for Assignment 1

## Project chosen

Name: pyglet

URL: https://github.com/pyglet/pyglet

Number of lines of code and the tool used to count it: 100531, calculated by Lizard:
<img width="640" alt="Screenshot 2024-06-27 at 11 42 34" src="https://github.com/sannedb/pyglet/assets/90255780/c267df1a-7ac9-4dfb-917d-d4fce0d34ae4">

Programming language: Python

## Coverage measurement

### Existing tool

<Inform the name of the existing tool that was executed and how it was executed>
We used coverage.py as recommended by the coordinators. Pyglet instructed to only run the unit tests by calling pytest on their tests/unit directory, so we did just that. The commands were as follows:
  
```
# installing necessities
python3 -m pip install coverage
pip install --upgrade --user pyglet
pip install -r tests/requirements.txt --user

# running test and gathering results
coverage run --branch -m pytest tests/unit
coverage html
```
This resulted in the following coverage:
<Show the coverage results provided by the existing tool with a screenshot>
<img width="855" alt="Screenshot 2024-06-27 at 13 03 59" src="https://github.com/sannedb/pyglet/assets/90255780/71156523-f3cc-4482-b554-67e1f87128b6">
<img width="1129" alt="Screenshot 2024-06-27 at 13 03 31" src="https://github.com/sannedb/pyglet/assets/90255780/9a290a27-bf33-4a6a-8b44-ca7066982862">



### Your own coverage tool

<The following is supposed to be repeated for each group member>

Sanne

get_document.py

https://github.com/sannedb/pyglet/commit/b4bc00c405f50ee607d8b7c33ead8e892f292338

<Provide a screenshot of the coverage results output by the instrumentation>

<Function 2 name>

<Provide the same kind of information provided for Function 1>

Sepaanta

<Function 1 name>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>

<Provide a screenshot of the coverage results output by the instrumentation>

<Function 2 name>

<Provide the same kind of information provided for Function 1>

Emilija

<Function 1 name>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>

<Provide a screenshot of the coverage results output by the instrumentation>

<Function 2 name>

<Provide the same kind of information provided for Function 1>

Rūta

<Function 1 name>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>

<Provide a screenshot of the coverage results output by the instrumentation>

<Function 2 name>

<Provide the same kind of information provided for Function 1>

## Coverage improvement

### Individual tests

<The following is supposed to be repeated for each group member>

Sanne

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Provide the same kind of information provided for Test 1>

Sepaanta

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Provide the same kind of information provided for Test 1>

Emilija

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Provide the same kind of information provided for Test 1>

Rūta

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Provide the same kind of information provided for Test 1>

### Overall

<Provide a screenshot of the old coverage results by running an existing tool (the same as you already showed above)>
<img width="855" alt="Screenshot 2024-06-27 at 13 03 59" src="https://github.com/sannedb/pyglet/assets/90255780/398aa74d-b022-4457-91ab-9afd48c64fa5">

<Provide a screenshot of the new coverage results by running the existing tool using all test modifications made by the group>

## Statement of individual contributions

Sanne: Tested the NLOC for this document, ran the coverage tool for this document, instrumented and tested coverage for get_document and handle_answers <br/>
Sepaanta: Found the project, ran the initial coverage test, ... <br/>
Emilija: Ran the initial NLOC check, ... <br/>
Rūta: ... <br/>
