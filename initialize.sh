wget http://qa.mpi-inf.mpg.de/convex/data.zip
unzip data.zip
rm data.zip
wget http://gaia.infor.uva.es/hdt/wikidata/wikidata2018_09_11.hdt.gz
unzip wikidata2018_09_11.hdt.gz
mv wikidata2018_09_11.hdt data
wget http://qa.mpi-inf.mpg.de/convex/ConvQuestions_test.zip
unzip ConvQuestions_test.zip -d data/
