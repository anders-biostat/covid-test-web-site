German text for all web pages:

Entry page
==========

University logo on top right.

Page title: "Schnelltest der Universität Heidelberg auf das Covid-19-Coronavirus (SARS-CoV-2)" 

- Button "Ich habe ein Test-Kit erhalten." (Image of a test kit above button)  -> button links to *Consent page*

- Button "Ich möchte mein Test-Ergebnis abfragen"  -> button links to *Result query page*

- Button "Ich möchte mehr über den Test erfahren"  -> button links to "Information page*

- small at the bottom: Link to Impressum page


Consent Page
================

"Bevor Sie an diesem Tst teilnehmen können, lesen Sie bitte den folgenden Aufklärungs-Text. Bite erklären Sie dann Ihr Einverständnis mit der Schaltfläche **am Ende der Seite**"

- insert lengthy text for informed consent here, possible in a frame with a vertical scrollbar

Button: "Ich bin einverstanden und möchte am Test teilnehmen"  -> links to *Registration page*


Registration page
=================

Bitte geben Sie den Code auf Ihrem Proben-Röhrchen an:


Code auf dem Röhrchen: _______  [Next to this field, an image of a test tube with an arrow or a box highlighting the code]

Falls Sie kein Röhrchen mit Code erhalten haben, klicken Sie bitte [hier].



Falls wir das Virus in Ihrer Probe nachweisen sollten, muss das Gesundheitsamt Sie erreichen können. Geben Sie daher bitte Ihre Kontakt-Daten an:

Name: _______________________

Anschrift (Strasse, Hausnummer, Wohnort) : ___________________________________________

Telefonnummer **oder** E-Mail-Adresse: ______________________________________________

(in smaller font) Datenschutz-Hinweis: Ihr Name und Ihre Kontaktdaten werden streng vertraulich behandelt. Nur die Mitarbeiter des Gesundheitsamts haben darauf Zugriff. 


Damit Sie selbst Ihr Ergebnis abfragen können, *notieren Sie sich bitte ihren Code* und geben Sie ein Passwort an:

Passwort: ________________      dasselbe Passwort nochmal: _________________


[ Daten abschicken ]

This button checks that the code is valid (for now: precisely 6 letters, nothing else), and that the two passwords agree, and then sends the data as HTTP form data to the server. The server stores the data in a CSV file, after encryting the password, together with a time stamp. Then, the *Instructions page* is shown


Instructions page
=================

Bitte sehen Sie sich das folgende kurze Video an, um zu erfahren, was Sie nun machen müssen. 

[Box with video]

Wenn Sie das Röhrchen befüllt haben, wie im Video gezeigt, leiten Sie uns das Röhrchen bitte wie folgt zu

Rückgabe-Anweisung für Test-Gruppe [designation of the test group]: [return instruction for test group]

(Return instructions are taken from a table that maps codes to instruction sentences. For each test group (= group of codes that has been handed out together), it is a sentence like "Please return it until Monday morning to your company's receptionist" or "Please use the provided envelope to mail it to ZMBH, Im Neuenheimer Feld 282, Heidelberg" -- or the like.)

Vielen Dank für Ihre Teilnahme.

Morgen oder übermorgen können Sie Ihr Ergebnis hier [link to *results query page*] abfragen. Notieren Sie sich dazu Ihren Code und Ihr Passwort.



Results query page
==================

Hier können Sie das Ergebnis Ihres Covid19-Tests abfragen:

Ihr Code: __________  (wie er auf Ihrem Röhrchen aufgedruckt war)

Ihr Passwort: ______________  (wie Sie es bei der Eingabe Ihrer Daten gewählt haben)

Button "Ergebnis anzeigen"

The button displays one of the pages *Negative result page*, *Positive result page*, *No result yet page* *Wrong password*, *Unknown code*


Negative results page
=====================

In Ihrer Probe konnte das Coronavirus SARS-CoV-2 **nicht** nachgewiesen werden. Vermutlich sind Sie also nicht mit Covid-19 infiziert.

**Bedenken Sie aber:**
- Unser Test ist nicht perfekt und nicht so genau wie der "offizielle" PCR-Test. Daher kommt es vor, dass der Test Infektionen übersieht.
- Selbst, wenn Ihre Probe wirklich keinen Virus enthielt: Vielleicht war das Virus nicht in Ihrem Speichel, aber anderswo im Körper. Oder Sie haben sich in den letzten Tagen angesteckt, erst nachdem Sie die Probe abgegeben haben. Oder Sie treffen morgen jemanden, der Sie ansteckt.

**Daher:** Seien Sie weiterhin vorsichtig. Halten Sie Abstand zu anderen, tragen Sie in der Öffentlichkeit eine Maske, und beachten Sie weiterhin alle Regelungen zur vermeidung von Ansteckungen.


Positive result page
====================

Ihre Probe war **positiv**. Das heisst, das in Ihrer Probe das Coronavirus SARS-CoV-2 nachgewiesen wurde und Sie sich wahrscheinlich mit Covid-19 angesteckt haben.

Bitte bleiben Sie zu Hause und vermeiden Sie jeglichen Kontakt zu anderen. Wenn Sie ärztlichen Rat wünschen, wenden Sie sich bitte (per Telefon!) an Ihren Hausarzt.

Ein Mitarbeiter des Gesundheitsamtes wird sich baldmöglichst mit Ihnen in Verbindung setzen und das weitere Vorgehen mit Ihnen besprechen. Sie können auch selbst die Corona-Hotline des Gesundheitsamtes anrufen: 06221 522-1881.


No result yet page
==================

Für Ihre Probe liegt leider noch kein Ergebnis vor. Bitte versuchen Sie es später oder morgen noch einmal.


Wrong password page
===================

Das von Ihnen eingegeben Passwort passt nicht zu Ihrem Code. Vielleicht haben Sie sich vertippt? Bitte versuchen Sie es noch einmal.  (Button "Zurück" links back to *Results query page*)


No-tube Page
============

Unsere Test-Kits bestehen aus einem größeren Röhrchen mit salzigem Wasser, einem kleinen Röhrchen mit aufgedrucktem Code, und einer Plastik-Pipette.

Wir verteilen diese Kits im Rahmen von Test-Aktionen, z.B. an alle Mitarbeiter einer Einrichtung. Nur wer auf solchem Wege ein Test-Kit erhalten hat, kann teilnehmen. 

Bitte verstehen Sie, dass sich der Aufwand einer Test-Aktion nur lohnt, wenn wir dadurch eine größere Zahl Personen testen können. Für Einzel-Personen können wir den test leider nicht anbieten. Wenn Sie uns aber helfen möchten, und für eine größere Gruppe die verteilung von test-Kits organisieren möchten, wenden Sie sich doch mit einem Vorschlag an uns. [Link to Impressum Page]


Information Page
================

Schön, dass Sie sich für unsere Test-Aktion interessieren. Der folgende Text dient sowohl als allgemeine Information, als auch zur Aufklärung der Teilnehmer:

[Lengthy information text goes here]


Impressum Page
==============

Diese Studie wird organisert vom 

Zentrum für Molekularbiologie der 
Universität Heidelberg (ZMBH)
Im Neuenheimer Feld 282
69120 Heidelberg

in Zusammenarbeit mit dem

Gesundheitsamt Rhein-Neckar-Kreis
Kurfürsten-Anlage 38-40
69115 Heidelberg 

Für Anfragen wenden Sie sich bitte an
- Prof. Michael Knop, m.knop@zmbh.uni-heidelberg.de, oder
- Dr. Simon Anders, s.anders@zmbh.uni-heidelberg.de,
beide am ZMBH
(highlight the paragraph with contact information)


Für detaillierte Informationen zur Studie lesen Sie bitte unseren *Informationstext* [Link to Information Page]

Verantwortlicher Leiter der Studie ist Prof. Knop. Verantwortlich für die Webseite ist Dr. Anders. Die Studie wurde von der Ethikkomission der Universität Heidelberg (Aktenzeichen (to be filled in)) befürwortet. Hinweise zum Datenschutz finden Sie im *Informationstext* [Link to Information Page].

