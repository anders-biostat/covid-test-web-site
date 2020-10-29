## Plan for migration of Covid test server from old software (papagei) to Lennard's new software (HeiCloud)

1. Perform a few registrations of test codes on the old production server. Set results for some of them.

2. Define current time as "main freeze". Copy content of "code_batches/" folder and the content of "results.txt" from old to new server. Now, no new barcode batches may be added to the "code_batches/" directory and no new results may be added on papagei without keeping a note to manually do this also on the new server afterwards. 

2. Run script "xxxx.py" to enter all the codes from the copied "code_batches" folder to the MongoDB data base. -> Now, the database contains a document for each bar code printed so far, with status "printed" and current time stamp.

3. Run script "xxxx.py" to enter all results from the old "results.txt", appropriately converting statuses as shown in Table 1 below

4. Define current time as "subject soft-freeze". Copy subjects.csv file to new server.

5. Run script "xxxx.py" to enter all the registrations into the database from subjects.csv into the data base.

6. Test the entries from step 1 on the new server, also test registration of further test codes.

7. Thoroughly test new production server.

8. Verify on old server that none of the files in the "code_batches" directory has a last-change time stamp later than the main freeze time point. 

9. Verify on old server that the last-change time stamp of file "results.txt" is no later than the main freeze time point. 

10. Check on old server whether the last-change time stamp of file "subjects.csv" is later than the main freeze time point. If so, copy the line since added to the new server, run script "xxx.py" again on them to add them to the data base.

11. Set redirect from old server to new server. Stop FastCGI process on old server.

12. Redo items 8 to 10.

