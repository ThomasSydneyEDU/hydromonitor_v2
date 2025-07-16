const functions = require("firebase-functions");
const { setGlobalOptions } = require("firebase-functions");
const admin = require("firebase-admin");
const cors = require("cors")({
  origin: ["https://hydroweb-fe1ae.web.app"],
});
admin.initializeApp();

const db = admin.firestore();
setGlobalOptions({ maxInstances: 10 });

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
        res.status(404).json({ error: "No data found" });
        return;
      }

      const rawData = snapshot.docs[0].data();
      const data = { ...rawData };

      res.json({
        ...data,
        timestamp_local:
          data.timestamp_local !== undefined && data.timestamp_local !== null
            ? data.timestamp_local
            : null,
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
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
        res.status(404).json({ error: "No data found" });
        return;
      }

      const history = snapshot.docs.map((doc) => {
        const data = doc.data();
        return {
          timestamp: data.timestamp ? data.timestamp : null,
          timestamp_local:
            data.timestamp_local !== undefined && data.timestamp_local !== null
              ? data.timestamp_local
              : null,
          air_temp_indoor: data.air_temp_indoor,
          air_temp_outdoor: data.air_temp_outdoor,
          humidity_indoor: data.humidity_indoor,
          humidity_outdoor: data.humidity_outdoor,
          water_temp_top: data.water_temp_top,
          water_temp_bottom: data.water_temp_bottom,
        };
      });

      res.json(history);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
});

// Image serving function
const { Storage } = require("@google-cloud/storage");
const storage = new Storage();

exports.getImage = functions.https.onRequest((req, res) => {
  cors(req, res, async () => {
    const camera = req.query.camera;

    if (!["top", "bottom"].includes(camera)) {
      res.status(400).send("Invalid camera type.");
      return;
    }

    const bucketName = "hydroweb-fe1ae.appspot.com"; // ✅ Correct bucket name
    const filename =
      camera === "top"
        ? "daily-images/TopCamera.jpg"
        : "daily-images/BottomCamera.jpg";
    const bucket = storage.bucket(bucketName);
    const file = bucket.file(filename);

    try {
      const [exists] = await file.exists();
      if (!exists) {
        res.status(404).send("Image not found.");
        return;
      }

      res.setHeader("Content-Type", "image/jpeg");
      file
        .createReadStream()
        .pipe(res)
        .on("error", (err) => {
          console.error(err);
          res.status(500).send("Error streaming image.");
        });
    } catch (err) {
      console.error(err);
      res.status(500).send("Error fetching image.");
    }
  });
});