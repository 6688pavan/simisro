import json

class ConfigManager:
    def save_config(self, filepath, parameters, simulation_settings):
        config = {
            "simulation_settings": simulation_settings,  # start_time, end_time, hz
            "parameters": [p.to_dict() for p in parameters]
        }
        with open(filepath, "w") as f:
            json.dump(config, f, indent=4)

    def load_config(self, filepath):
        with open(filepath, "r") as f:
            config = json.load(f)
        params = [Parameter.from_dict(p) for p in config["parameters"]]
        return config.get("simulation_settings", {}), params
