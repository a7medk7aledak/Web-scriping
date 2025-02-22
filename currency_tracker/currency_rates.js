const axios = require("axios");
const fs = require("fs");
const path = require("path");

const LOG_PREFIX = "[Currency Rates]";
const API_URL = "https://api.exchangerate-api.com/v4/latest/EGP";
const FILE_PATH = path.join(__dirname, "currency_rates.json");
const UPDATE_INTERVAL = 300000; // Update every 5 minutes

async function getCurrencyRates() {
  try {
    const { data } = await axios.get(API_URL);

    // Check if data exists
    if (!data || !data.rates) {
      throw new Error("Exchange rates data not found");
    }

    // Convert rates to be relative to the Egyptian Pound
    const currencies = {
      USD: (1 / data.rates.USD).toFixed(4),
      EUR: (1 / data.rates.EUR).toFixed(4),
      GBP: (1 / data.rates.GBP).toFixed(4),
      SAR: (1 / data.rates.SAR).toFixed(4),
    };

    console.log(
      `${LOG_PREFIX} Successfully retrieved exchange rates:`,
      currencies
    );
    return currencies;
  } catch (error) {
    console.error(`${LOG_PREFIX} Error fetching data:`, error.message);
    return null;
  }
}

function saveToJson(data) {
  try {
    const newEntry = {
      timestamp: new Date().toISOString(),
      rates: data,
      source: "Exchange Rate API",
    };

    // Read existing file if available
    let history = [];
    if (fs.existsSync(FILE_PATH)) {
      const fileContent = fs.readFileSync(FILE_PATH, "utf-8");
      history = JSON.parse(fileContent);
      if (!Array.isArray(history)) {
        history = [history];
      }
    }

    // Add new data and keep only the last 100 updates
    history.unshift(newEntry);
    if (history.length > 100) {
      history = history.slice(0, 100);
    }

    fs.writeFileSync(FILE_PATH, JSON.stringify(history, null, 2), "utf-8");
    console.log(`${LOG_PREFIX} Data saved successfully`);
  } catch (error) {
    console.error(`${LOG_PREFIX} Error saving data:`, error.message);
  }
}

async function main() {
  console.log(`${LOG_PREFIX} Fetching exchange rates...`);
  try {
    const rates = await getCurrencyRates();
    if (rates) {
      saveToJson(rates);
    } else {
      console.log(`${LOG_PREFIX} No exchange rates found`);
    }
  } catch (error) {
    console.error(`${LOG_PREFIX} Unexpected error:`, error.message);
  }
}

// Add a random delay between requests
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function loop() {
  await main();
  // Random delay between 4-6 minutes
  const randomDelay = Math.floor(Math.random() * (360000 - 240000) + 240000);
  setTimeout(loop, randomDelay);
}

// Start execution
loop();
