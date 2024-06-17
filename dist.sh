cp -v *.py config.py constants.py D*.py I*.py M*.py B*.py F*.py V*.py Inst*.py ../4xenblocks-Assistant
cp *.py config.py constants.py D*.py T*.py M*.py B*.py F*.py V*.py Inst*.py ../3xenblocks-Assistant
cp *.py config.py constants.py D*.py T*.py M*.py B*.py F*.py V*.py Inst*.py ../2xenblocks-Assistant
cp *.py config.py constants.py D*.py T*.py M*.py B*.py F*.py V*.py Inst*.py ../temp

cp -r graphs ui db views statemachine integrationtest ../4xenblocks-Assistant/
cp -r graphs ui db views statemachine integrationtest ../3xenblocks-Assistant/
cp -r graphs ui db views statemachine integrationtest ../2xenblocks-Assistant/
cp -v -r graphs ui db views statemachine integrationtest ../temp/

