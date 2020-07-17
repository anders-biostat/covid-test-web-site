We need web pages as follows:

Entry page
==========

Welcome to the Covid-19 Rapid Test.

If you have been handed a test kit [image of a tube], please click here to learn more about how to participate: [button]

/ Button lead to Information page


Information Page
================

Before participating, please read the following informationm, then press the button at the very bottom of the page

[insert lengthy text for informed consent here]

[Button: "Ich bin einverstanden und möchte am Test teilnehmen"]

/ Button leads to next page


Registration page
=================

Please enter here the code on the label of ytour test tube: [______]

(If you have not yet been given a tube, pleaser click here: [Link to "no-tube" page])

In case your sample is positive we must be able to contact you. Hence, please enter your details below:

Vorname und Nachname: __________________________________

Adresse (Strasse, Hausnummer, Ort): ________________________________

E-Mail-Adresse oder Telefonnummer: ______________________________________

[ Registrieren ]

/ Button "Regsitrieren" checks that the code is valid (for now: precisely 6 letters, nothing else ), then send the 
/ data as HTTP form data to the server, and loads instruction page


Instruction page
================

Code: ABCDEF

Please watch the following short video with instructions

[Box with video]

Once you have taken the sample (as shown in the video), please return the sample as follows

Sample return instruction:

/ Return instructions are taken from a table that maps codes to instruction sentences. For each cohort (= group of codes that has been handed out together), it is a sentence like "Please return it until Monday morning to your company's receptionist" or "Please use the provided envelope to mail it to ZMBH, Im Neuenheimer Feld 282, Heidelberg" -- or the like.

as this page [insert link to Results Page], you can get your result in a day or two


Results Page
============

Please enter your code: _________

[Check results]   -> This button checks the result and then displays one of the pages positive.html or negative.html


No-tube Page
============

Sorry, if you have not been handed a tube, you cannot participate.

We hand the tubes to organisations (companies, schools, etc) to distribute among their members. If you are interested to have your organisatioon participate, please contact us: [Link to Impressum]


Impressum Page
==============

This study is organized by: Prof M Knop, address, phone number, ...

