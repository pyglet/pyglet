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
We used Coverage (coverage.py) as recommended by the coordinators. Pyglet instructed to only run the unit tests by calling pytest on their tests/unit directory, so we did just that. The commands to execute the tests were as follows:
  
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

<img width="788" alt="Screenshot 2024-06-27 at 14 25 56" src="https://github.com/sannedb/pyglet/assets/90255780/b4cbe265-e94b-420b-8af1-b06e776807a7">

<br/>


handle_answer.py

https://github.com/sannedb/pyglet/commit/b4bc00c405f50ee607d8b7c33ead8e892f292338

<img width="786" alt="Screenshot 2024-06-27 at 14 26 05" src="https://github.com/sannedb/pyglet/assets/90255780/2f54ffbe-6d8e-42dd-a00d-1478dbb05a4b">

Sepaanta

limit.py

https://github.com/sannedb/pyglet/commit/68bec1593026c784580dc821d2a7b42e9738bdf1

<Provide a screenshot of the coverage results output by the instrumentation>

<img src="https://github.com/sannedb/pyglet/assets/92684792/cc98025d-9248-401b-9c75-9fd1d0591450">

<br/>
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

Test 1: get_document.py

https://github.com/sannedb/pyglet/commit/9e643251d0b8139fafc9ac9fa928f2d5c7a3e1f0 

<img width="788" alt="Screenshot 2024-06-27 at 14 25 56" src="https://github.com/sannedb/pyglet/assets/90255780/2b7349ae-6bf8-4a94-928e-9a686d3cbb15">

<img width="798" alt="Screenshot 2024-06-27 at 14 32 28" src="https://github.com/sannedb/pyglet/assets/90255780/4e885b8b-f32d-4bbc-a270-60816103a4d4">

<br/>

The coverage is now 100%. In essence this was not too hard, because there can only be two situations: one where there is no document so they create one, and one where there is one and they return that. I created tests for both cases. The coverage was improved because it was 0% at first, which I am assuming is because either of the situations will always be true so creating a test for this function may not have had the highest priority for Pyglet's developer team. Below you can find the proof of improvement after checking with coverage.py:

<br/>

<img width="1098" alt="Screenshot 2024-06-27 at 14 52 23" src="https://github.com/sannedb/pyglet/assets/90255780/a53c67fb-f149-4484-809b-7c5f0d599c1a">
<img width="1135" alt="Screenshot 2024-06-27 at 14 53 19" src="https://github.com/sannedb/pyglet/assets/90255780/67250345-09a2-42c4-8ed1-04fb91a2a870">

<br/>

Test 2: handle_answer.py

https://github.com/sannedb/pyglet/commit/9e643251d0b8139fafc9ac9fa928f2d5c7a3e1f0 

<img width="786" alt="Screenshot 2024-06-27 at 14 26 05" src="https://github.com/sannedb/pyglet/assets/90255780/5aced0f7-ce5e-44bd-b4d2-fabf543ca1ad">

<br/>

The coverage for this function is now at 95%. I have created mock situations, that will print statements addressing what the error is, rather than raising the actual error, so that the testing can proceed without the file shutting down. Once again, there was no test made for it to begin with so its initial coverage was at 0%, meaning the coverage would have improved regardlessly even if i were to check just the 'None' situation. Below you can find the proof of improvement after checking with coverage.py:

<br/>

<img width="943" alt="Screenshot 2024-06-27 at 14 43 51" src="https://github.com/sannedb/pyglet/assets/90255780/5af94469-7c1c-48fa-8dac-0010a6217449">
<img width="944" alt="Screenshot 2024-06-27 at 14 44 18" src="https://github.com/sannedb/pyglet/assets/90255780/d7f4e2b8-b501-4c36-89bd-243dd8187a8b">

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

Sanne: 
* Tested the NLOC for this document;
* ran the coverage tool for this document;
* instrumented and tested coverage for get_document and handle_answers;
* handled README.md structure.

Sepaanta: 
* Found the project;
* ran the initial coverage test;
* ...

Emilija: 
* Ran the initial NLOC check;
* ...

Rūta:
* ...
