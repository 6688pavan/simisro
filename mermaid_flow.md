sequenceDiagram
    participant Main as main.py
    participant MW as MainWindow
    participant PE as ParameterEditor
    participant PT as ParameterTable
    participant WP as WaveformPlot
    participant LV as LogView
    participant ST as SeederThread
    participant SNT as SenderThread
    participant SE as SeedingEngine
    participant PB as PacketBuffer
    participant WF as Waveform
    participant LD as Loader
    participant CFG as ConfigManager
    participant MS as MulticastSender

    Note over Main,MS: Application Startup & Initialization
    Main->>MW: Create MainWindow
    activate MW
    MW->>MW: Load style.qss theme
    MW->>PT: Initialize ParameterTable
    activate PT
    MW->>WP: Initialize WaveformPlot
    activate WP
    MW->>LV: Initialize LogView
    activate LV
    MW->>Main: Show window
    
    Note over Main,MS: Configuration & Data Loading (JSON)
    MW->>CFG: load_config(json_path)
    activate CFG
    CFG-->>MW: settings + parameters
    deactivate CFG
    MW->>PT: load_parameters(params)
    PT-->>MW: Parameters loaded
    MW->>MW: Apply settings (start/end time, hz)
    
    MW->>LD: load_dat(file)
    activate LD
    LD-->>MW: dat_buffer + params
    deactivate LD
    MW->>PT: update_parameters(params)
    
    Note over Main,MS: Parameter Management (Edit & Export JSON)
    MW->>PE: Open ParameterEditor
    activate PE
    PE-->>MW: Parameter updated/added
    deactivate PE
    MW->>PT: add/update_row(param)
    PT-->>MW: Table updated
    MW->>CFG: save_config(json_path, parameters, settings)
    activate CFG
    CFG-->>MW: JSON written
    deactivate CFG
    
    Note over Main,MS: Start Seeding & Transmission
    MW->>SNT: start(group, port)
    activate SNT
    SNT->>SNT: Configure UDP socket
    SNT-->>MW: Sender ready
    
    MW->>ST: start(start_time, end_time, hz)
    activate ST
    ST-->>MW: Seeder started
    
    Note over Main,MS: Record Generation Loop (1/hz rate)
    loop Each record at interval 1/hz
        ST->>ST: Calculate time increment
        ST->>SE: seed_record(params, t, dat_buffer, Δt)
        activate SE
        
        SE->>PB: Create PacketBuffer
        activate PB
        SE->>PB: set_record_time(t)
        
        alt Minor Cycle (5 samples)
            SE->>WF: make_waveform(params)
            activate WF
            WF-->>SE: waveform data
            deactivate WF
            SE->>PB: write_samples(5 samples, offsets)
            SE->>MW: sample_generated(name, values, t)
            MW->>PT: update_instantaneous(name, values, times)
            MW->>WP: update_waveform(params, t, Δt)
            
        else Major Cycle (1 sample)
            SE->>WF: make_waveform(params)
            activate WF
            WF-->>SE: waveform data
            deactivate WF
            SE->>PB: write_sample(1 sample, offset)
            SE->>MW: sample_generated(name, value, t)
            MW->>PT: update_instantaneous(name, value, t)
            MW->>WP: update_waveform(params, t, Δt)
        end
        
        PB-->>SE: get_packets()
        deactivate PB
        SE-->>ST: packets ready
        deactivate SE
        
        ST->>MW: record_ready(idx, t, packets)
        MW->>SNT: enqueue(idx, packets)
        SNT->>SNT: queue.put() & wait
        
        SNT->>MS: sendto(packets)
        activate MS
        MS-->>SNT: bytes sent
        deactivate MS
        
        SNT->>MW: record_sent(idx, timestamp)
        MW->>MW: Update statistics
        MW->>LV: Log transmission
    end
    
    Note over Main,MS: Playback Control
    MW->>ST: pause_event.clear()
    MW->>SNT: pause_event.clear()
    Note right of ST: Paused
    
    MW->>ST: pause_event.set()
    MW->>SNT: pause_event.set()
    Note right of ST: Resumed
    
    Note over Main,MS: Shutdown
    MW->>ST: stop() & wait()
    deactivate ST
    MW->>SNT: stop() & enqueue(None)
    deactivate SNT
    
    deactivate LV
    deactivate WP
    deactivate PT
    deactivate MW