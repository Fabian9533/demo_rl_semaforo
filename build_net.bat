@echo off
REM Regenera las redes SUMO a partir de nodos/vias (solo si editas los .nod.xml / .edg.xml / .con.xml)
netconvert --node-files cruce.nod.xml --edge-files cruce.edg.xml --output-file cruce.net.xml --no-turnarounds --tls.green.time 25
netconvert --node-files cruce2.nod.xml --edge-files cruce2.edg.xml --connection-files cruce2.con.xml --output-file cruce2.net.xml --no-turnarounds --tls.green.time 20 --tls.left-green.time 6
netconvert --node-files corredor.nod.xml --edge-files corredor.edg.xml --output-file corredor.net.xml --no-turnarounds --tls.green.time 25
netconvert --node-files red.nod.xml --edge-files red.edg.xml --output-file red.net.xml --no-turnarounds --tls.green.time 20
REM malla3 (plan v2, P5): 3x3 cruces, 2 carriles por sentido; cada semaforo con 2 fases verdes y ambar de 3 s
netconvert --node-files malla3.nod.xml --edge-files malla3.edg.xml --output-file malla3.net.xml --no-turnarounds --tls.green.time 20
pause
