# kvm-compute-service


## Formato messaggi

Messaggi JSON

{"type":int,"value":string}

valori per type per il nodo server

* 0 Avvia una VM value -> {"zone":"zone_uuid","name":"vmname","type":"vmtype"}
* 1 Distruggi una VM value -> {'uuid':'vmuuid'}
* 2 Aggiungi una zona value -> {"name":"zone-name","uuid":"zone-uuid","address":"zone-ip-address","port":"zone-tcp-port"}
* 3 Distruggi una zona value -> {'uuid':'zone-uuid'}
* 4 Lista delle vm value -> Null
* 5 Lista delle zone value -> Null
* 6 Lista dei tipo di vm value -> Null
* 7 Ping value -> Null
* 8 Pong value -> Null
* 10 Chiusura connessione value -> Null



Valori per type nodo di compute

* 0 Avvia una VM value -> {"name":"vmname","type":"vmtype"}
* 1 Distruggi una VM value -> {'uuid':'vmuuid'}
* 4 Distruggi una zona value -> Null
* 7 Ping value -> Null
* 8 Pong value -> Null
* 10 Chiusura connessione value -> Null


Valori per le rispose
* 9 Errore value -> {'status':false,'error':'error description'}
* 11 Informazione vm value -> {"name":name,"address":mac,"uuid":vm_uuid,"ip":ip,"status":int}

	Valori per status
		* 0 Booting
		* 1 Running
		* 2 Killed

* 12 informazione gernerica value -> {'status':bool,'res':json}
	res può essere null
Valore di type riservato 99
