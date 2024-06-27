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

<img src="https://github.com/sannedb/pyglet/assets/92684792/cc98025d-9248-401b-9c75-9fd1d0591450">

<br/>

normalize.py

<Provide the same kind of information provided for Function 1>
https://github.com/sannedb/pyglet/commit/0db04da130f651e0849d77826ba2a974ef476993

<img src="https://github.com/sannedb/pyglet/assets/92684792/f30ac9c5-c229-4e33-8fa1-26c7219c24b6">

Emilija

inverse.py

https://github.com/sannedb/pyglet/commit/50ee8a173c09bc9bbfecc37ad67fdf1ce6cda241

<img width="263" alt="Screenshot 2024-06-27 at 21 49 51" src="https://github.com/sannedb/pyglet/assets/89348302/54e4bb6c-ef9e-4ce8-ac76-465ca6193509">

on_key_press.py

https://github.com/sannedb/pyglet/commit/33fbb3e8d2ae0e39e8671a59c7ed0c085571a4b0

Rūta

draw_text.py

https://github.com/pyglet/pyglet/commit/423262dba9547773da371a9ad5f36e63e7455f75

<img width="889" alt="Screenshot 2024-06-27 at 23 23 51" src="https://github.com/sannedb/pyglet/assets/55755724/98e650ab-c085-488a-9a6d-651ed10a2647">

tear_down.py

https://github.com/sannedb/pyglet/commit/cbda5d030a0bf155ae8cc6e51892bb93cca1209c
<img width="883" alt="Screenshot 2024-06-27 at 23 24 19" src="https://github.com/sannedb/pyglet/assets/55755724/98bce27d-9180-48c3-87af-429bf071526a">


## Coverage improvement

### Individual tests

<The following is supposed to be repeated for each group member>

Sanne

Test 1: get_document.py

https://github.com/sannedb/pyglet/commit/9e643251d0b8139fafc9ac9fa928f2d5c7a3e1f0 

<img width="788" alt="Screenshot 2024-06-27 at 14 25 56" src="https://github.com/sannedb/pyglet/assets/90255780/2b7349ae-6bf8-4a94-928e-9a686d3cbb15">

After:

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

After:

<img width="622" alt="Screenshot 2024-06-27 at 17 51 18" src="https://github.com/sannedb/pyglet/assets/90255780/07993b33-93b9-421b-a65a-3490fb77ce8f">


<br/>

The coverage for this function is now at 95%. I have created mock situations, that will print statements addressing what the error is, rather than raising the actual error, so that the testing can proceed without the file shutting down. Once again, there was no test made for it to begin with so its initial coverage was at 0%, meaning the coverage would have improved regardlessly even if i were to check just the 'None' situation. Below you can find the proof of improvement after checking with coverage.py:

<br/>

<img width="943" alt="Screenshot 2024-06-27 at 14 43 51" src="https://github.com/sannedb/pyglet/assets/90255780/5af94469-7c1c-48fa-8dac-0010a6217449">
<img width="944" alt="Screenshot 2024-06-27 at 14 44 18" src="https://github.com/sannedb/pyglet/assets/90255780/d7f4e2b8-b501-4c36-89bd-243dd8187a8b">

Sepaanta

Test 1: limit.py

https://github.com/sannedb/pyglet/commit/3e7bc00ec4c81870041557bf3a7075998b088129 

old results:
<img src="https://github.com/sannedb/pyglet/assets/92684792/cc98025d-9248-401b-9c75-9fd1d0591450">

<br/>

<img src="https://github.com/sannedb/pyglet/assets/92684792/37a57dda-09fb-4ef7-b398-171b99063350">

<br/>

<img src="https://github.com/sannedb/pyglet/assets/92684792/4ec489c6-bfd9-457f-8334-1696c78ee1ad">

<br/>

the coverage is now 100% from 0%. There were no tests initially, which makes it easy to improve the coverage. I tested it with border values. One where the check is barely true and one where is barely false.

Test 2: normalize.py

<img src="https://github.com/sannedb/pyglet/assets/92684792/f30ac9c5-c229-4e33-8fa1-26c7219c24b6">

<br/>

https://github.com/sannedb/pyglet/commit/66b3d38f7262866df85445d3283d81b2109e5069

<img src="https://github.com/sannedb/pyglet/assets/92684792/9f0f273e-6cb2-4c11-a9ef-82da6336131c">

<br/>

<img src= "https://github.com/sannedb/pyglet/assets/92684792/c601d59c-8365-445c-8728-81d80ae09675">

The coverage is now 100% from 0%. There also weren't existing tests for this function. Which made it easy to improve


Emilija

Test 1: inverse.py

https://github.com/sannedb/pyglet/commit/50ee8a173c09bc9bbfecc37ad67fdf1ce6cda241

<img width="263" alt="Screenshot 2024-06-27 at 21 49 51" src="https://github.com/sannedb/pyglet/assets/89348302/54e4bb6c-ef9e-4ce8-ac76-465ca6193509">

<img width="1185" alt="Screenshot 2024-06-27 at 17 05 26" src="https://github.com/sannedb/pyglet/assets/89348302/0c6f4dfd-7b76-4a1d-bc10-4e44a0a6ad99">

<img width="979" alt="Screenshot 2024-06-27 at 20 49 32" src="https://github.com/sannedb/pyglet/assets/89348302/aa90ba04-cdf9-4533-bab1-7aad9a893a51">

The coverage went from 54% to 86%. Because the added test functions (test_inverse_of_zero_matrix and test_inverse_of_all_same_matrix) ensured that the branches in the inverse function were executed during the tests. 

Test 2: on_key_press

https://github.com/sannedb/pyglet/commit/33fbb3e8d2ae0e39e8671a59c7ed0c085571a4b0

<img width="969" alt="Screenshot 2024-06-27 at 20 51 03" src="https://github.com/sannedb/pyglet/assets/89348302/810e1f9e-defa-4e72-a852-fe58d3fb805d">
<img width="1028" alt="Screenshot 2024-06-27 at 20 52 13" src="https://github.com/sannedb/pyglet/assets/89348302/20c7f56a-83b3-4d15-94c4-4e8f8b97ac39">

The coverage went from 0% to 100% because the test function (test_on_key_press_pass) created ensured that the branches in on_key_press were executed.


Rūta

Test 1: draw_text.py

https://github.com/pyglet/pyglet/commit/423262dba9547773da371a9ad5f36e63e7455f75

<img width="889" alt="Screenshot 2024-06-27 at 23 23 51" src="https://github.com/sannedb/pyglet/assets/55755724/98e650ab-c085-488a-9a6d-651ed10a2647">

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

Test 2: tear_down.py

https://github.com/pyglet/pyglet/commit/cbda5d030a0bf155ae8cc6e51892bb93cca1209c

<img width="883" alt="Screenshot 2024-06-27 at 23 24 19" src="https://github.com/sannedb/pyglet/assets/55755724/98bce27d-9180-48c3-87af-429bf071526a">

### Overall

<img width="855" alt="Screenshot 2024-06-27 at 13 03 59" src="https://github.com/sannedb/pyglet/assets/90255780/398aa74d-b022-4457-91ab-9afd48c64fa5">

<Provide a screenshot of the new coverage results by running the existing tool using all test modifications made by the group>
<img width="737" alt="Screenshot 2024-06-27 at 23 26 48" src="https://github.com/sannedb/pyglet/assets/90255780/706cb23e-0e6a-4f34-a8f6-e17f13b37a82">


## Statement of individual contributions

Sanne: 
* Tested the NLOC for this document;
* ran the coverage tool for this document;
* instrumented and tested coverage for get_document and handle_answers;
* handled README.md structure.

Sepaanta: 
* Found the project;
* ran the initial coverage test;
* instrumented and tested coverage for limit.py and normalize.py

Emilija: 
* Ran the initial NLOC check;
* Ran initial coverage report;
* instrumented and tested coverage for inverse and on_key_press.

Rūta:
* instrumented and tested coverage for draw_text and tear_down;
