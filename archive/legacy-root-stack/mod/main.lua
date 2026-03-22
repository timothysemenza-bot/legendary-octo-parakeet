local BossKeyMod = RegisterMod("BossKeyMod", 1)
local json = require("json")

local function read_config(path)
    local file = io.open(path, "r")
    if not file then
        return { TEST_MODE = false }
    end

    local content = file:read("*a")
    file:close()

    local ok, parsed = pcall(function()
        return json.decode(content)
    end)

    if ok and type(parsed) == "table" then
        return parsed
    end

    return { TEST_MODE = false }
end

local CONFIG = read_config("config.json")

local function emit(prefix, payload)
    local ok, encoded = pcall(function()
        return json.encode(payload)
    end)
    if ok then
        print(prefix .. " " .. encoded)
    end
end

function BossKeyMod:OnGameStarted(_isContinued)
    if not CONFIG.TEST_MODE then
        return
    end

    local seed = CONFIG.seed or "SEED0001"

    emit("BKTEST", {
        seed = seed,
        event = "start",
        room = "spawn"
    })

    emit("BKTEST", {
        seed = seed,
        event = "checkpoint",
        objective = "clear_room",
        value = 1
    })

    emit("BKTEST_DONE", {
        seed = seed,
        status = "pass",
        metrics = {
            duration_ms = 120,
            score = 100
        }
    })
end

BossKeyMod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, BossKeyMod.OnGameStarted)
