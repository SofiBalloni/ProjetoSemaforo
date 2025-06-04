import { describe, expect, it } from "bun:test";

const apiURL = "http://localhost:4000"

describe("Teste da API", () => {
    const testSensor: Sensor = {
        sensorid: 123,
        zonas: [1, 2, 3],
        alagado: true,
    };

    it("Deve criar sensor", async () => {
        const response = await fetch(`${apiURL}/sensor/atualizar`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(testSensor),
        });
        expect(response.status).toBe(201);
    });

    it("Deve retornar o sensor criado", async () => {
        const response = await fetch(`${apiURL}/sensor/123`);
        expect(response.status).toBe(200);

        const sensor = <EpochSensor>await response.json();
        expect(sensor.sensorid).toBe(testSensor.sensorid);
        expect(sensor.zonas).toEqual(testSensor.zonas);
        expect(sensor.alagado).toBe(testSensor.alagado);
        expect(sensor.epoch).toBeGreaterThan(0);
    });

    it("Deve retornar todos os sensores, incluindo o que foi criado", async () => {
        const response = await fetch(`${apiURL}/sensor/listar`);
        expect(response.status).toBe(200);

        const sensors = <EpochSensor[]>await response.json();
        expect(sensors.length).toBeGreaterThan(0);
        const createdSensor = sensors.find((s) => s.sensorid === testSensor.sensorid);
        expect(createdSensor).toBeDefined();
        expect(createdSensor?.sensorid).toBe(testSensor.sensorid);
    });
})

interface Sensor {
    sensorid: number,
    zonas: number[],
    alagado: boolean,
}

interface EpochSensor extends Sensor{
    epoch: number
}