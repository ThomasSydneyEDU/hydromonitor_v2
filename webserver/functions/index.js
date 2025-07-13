const functions = require("firebase-functions");
const {setGlobalOptions} = require("firebase-functions");
const admin = require("firebase-admin");
const cors = require("cors")({
  origin: ["https://hydroweb-fe1ae.web.app"],
});
admin.initializeApp();

const db = admin.firestore();

setGlobalOptions({maxInstances: 10});

// Get latest sensor status
exports.getStatus = functions.https.onRequest((req, res) => {
  cors(req, res, async () => {
    try {
      const snapshot = await db
          .collection("Current Days Log")
          .orderBy("timestamp", "desc")
          .limit(1)
          .get();

      if (snapshot.empty) {
        res.status(404).json({error: "No data found"});
        return;
      }

      const rawData = snapshot.docs[0].data();
      const data = { ...rawData };

      res.json(data);
    } catch (error) {
      res.status(500).json({error: error.message});
    }
  });
});

// Get sensor history
exports.getHistory = functions.https.onRequest((req, res) => {
  cors(req, res, async () => {
    try {
      const snapshot = await db
          .collection("Current Days Log")
          .orderBy("timestamp")
          .get();

      if (snapshot.empty) {
        res.status(404).json({error: "No data found"});
        return;
      }

      const history = snapshot.docs.map((doc) => {
        const data = doc.data();
        return {
          timestamp: data.timestamp_local ?? null,
          air_temp_indoor: data.air_temp_indoor,
          air_temp_outdoor: data.air_temp_outdoor,
          humidity_indoor: data.humidity_indoor,
          humidity_outdoor: data.humidity_outdoor,
        };
      });

      res.json(history);
    } catch (error) {
      res.status(500).json({error: error.message});
    }
  });
});
