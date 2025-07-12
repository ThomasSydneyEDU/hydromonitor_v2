const functions = require("firebase-functions");
const {setGlobalOptions} = require("firebase-functions");
const admin = require("firebase-admin");
admin.initializeApp();

const db = admin.firestore();

setGlobalOptions({maxInstances: 10});

// Get latest sensor status
exports.getStatus = functions.https.onRequest(async (req, res) => {
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

                res.json(snapshot.docs[0].data());
        } catch (error) {
                res.status(500).json({error: error.message});
        }
});

// Get sensor history
exports.getHistory = functions.https.onRequest(async (req, res) => {
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
                                timestamp: data.timestamp
                                        ? data.timestamp.toDate().toISOString()
                                        : null,
                                "Air Temp (Indoor)": data["Air Temp (Indoor)"],
                                "Air Temp (Outdoor)": data["Air Temp (Outdoor)"],
                                "Humidity (Indoor)": data["Humidity (Indoor)"],
                                "Humidity (Outdoor)": data["Humidity (Outdoor)"],
                        };
                });

                res.json(history);
        } catch (error) {
                res.status(500).json({error: error.message});
        }
});
