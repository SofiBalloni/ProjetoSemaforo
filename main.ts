import { Database } from "bun:sqlite";

class AlagometrosDB extends Database{
    constructor(path:string){
        super(path)
    }
}

const db = new AlagometrosDB("data.db");

db.exec(await Bun.file("dbstart.sql").text())

Bun.serve({
  routes: {
    "/sensor/atualizar":{
      POST: async req => {
        let sensor = <Sensor>await req.json();
        let epoch = Date.now()*1000

        db.query(`INSERT INTO HistoricoSensores (epoch, sensorid, zonas, alagado) VALUES (?, ?, ?, ?)`,).run(epoch, sensor.sensorid, sensor.zonas.join(" "), sensor.alagado);
        return Response.json("OK", { status: 201 });
      },
    },

    "/sensor/listar": {
      GET: () => {
        let sensores = <DBSensor[]>db.query("SELECT * HistoricoSensores ORDER BY epoch DESC LIMIT 1").all();
        let sensoresIdentificados = new Set<number>();
        let sensoresFiltrados = sensores.filter((sensor)=>{
          if (sensoresIdentificados.has(sensor.sensorid)){
            return false
          } else {
            sensoresIdentificados.add(sensor.sensorid)
            return true
          }
        })
        let listaSensores: Sensor[] = []
        sensoresFiltrados.forEach(sensor=>{
          listaSensores.push(DBSensorToSensor(sensor))
        })
        return Response.json(sensores);
      }
    },
    "/sensor/:id": {
      GET: req => {
        let sensor = <DBSensor>db.query("SELECT * FROM HistoricoSensores WHERE sensorid = ? ORDER BY epoch DESC LIMIT 1").get(req.params.id);
        if (!sensor) {
          return new Response("Não Encontrado", { status: 404 });
        }
        return Response.json(sensor);
      }
    },
    "/zona/listar": {
      GET: () => {
        let zonas = <EpochSensor[]>db.query("SELECT * HistoricoZonas ORDER BY epoch DESC LIMIT 1").all();
        let zonaIdentificada = new Set<number>();
        return Response.json(zonas.filter((zona)=>{
          if (zonaIdentificada.has(zona.sensorid)){
            return false
          } else {
            zonaIdentificada.add(zona.sensorid)
            return true
          }
        }));
      }
    },
    "/zona/atualizar":{
      POST: async req => {
        const zona = <EpochZona>await req.json();
        const epoch = Date.now()*1000

        db.query(`INSERT INTO HistoricoZonas (epoch, zonaid, alagada) VALUES (?, ?, ?)`,).run(epoch, zona.zonaid, zona.alagada);
        return Response.json("OK", { status: 201 });
      },
    },
    "/zona/:id": {
      GET: req => {
        const zona = db.query("SELECT * FROM HistoricoZonas WHERE zonaid = ? ORDER BY epoch DESC LIMIT 1").get(req.params.id);
        if (!zona) {
          return new Response("Não Encontrada", { status: 404 });
        }
        return Response.json(zona);
      },
    }
  },

  error(error) {
    console.error(error);
    return new Response("Internal Server Error", { status: 500 });
  },
});

function DBSensorToSensor(dbsensor:DBSensor):Sensor{

}

function DBZonaToZona(dbsensor:DBSensor):Sensor{

}

interface Sensor {
    sensorid: number,
    zonas: number[],
    alagado: boolean,
}

interface EpochSensor extends Sensor{
    epoch?: number
}

interface DBSensor {
    sensorid: number,
    zonas: string,
    alagado: number,
    epoch: number
}

interface Zona {
    zonaid: number,
    alagada: boolean,
}

interface EpochZona extends Zona{
    epoch: number
}
db.query("").get()