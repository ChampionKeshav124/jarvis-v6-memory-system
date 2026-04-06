Add-Type -AssemblyName System.Speech
$recognition = New-Object System.Speech.Recognition.SpeechRecognitionEngine

# Configure the wake words
$choices = New-Object System.Speech.Recognition.Choices
$choices.Add("Jarvis")
$choices.Add("Jarvis wake up")
$choices.Add("Wake up Jarvis")
$choices.Add("Hello Jarvis")
$choices.Add("Hey Jarvis")
$choices.Add("Jarvis wake up daddys home")
$choices.Add("Jarvis uth jao")
$choices.Add("Service")
$choices.Add("Travis")
$choices.Add("Garvis")
$choices.Add("Jarvis are you there")

$builder = New-Object System.Speech.Recognition.GrammarBuilder
$builder.Append($choices)
$grammar = New-Object System.Speech.Recognition.Grammar($builder)

$recognition.LoadGrammar($grammar)
$recognition.SetInputToDefaultAudioDevice()

# Event Handlers
$action = {
    $result = $EventArgs.Result.Text
    Write-Host "WAKE_DETECTED:$result"
}

$levelAction = {
    $level = $EventArgs.AudioLevel
    # Only log if there's actually some sound to avoid spamming the console
    if ($level -gt 0) {
        Write-Host "AUDIO_LEVEL:$level"
    }
}

Register-ObjectEvent -InputObject $recognition -EventName "SpeechRecognized" -Action $action | Out-Null
Register-ObjectEvent -InputObject $recognition -EventName "AudioLevelUpdated" -Action $levelAction | Out-Null

$recognition.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)

Write-Host "SPEECH_LISTENER_STARTED"

# Keep alive & Resilient Re-Link loop
$counter = 0
while($true) { 
    Start-Sleep -Seconds 1 
    $counter++

    # 1. Heartbeat to let Electron know we're alive
    if ($counter % 10 -eq 0) {
        Write-Host "HEARTBEAT"
    }

    # 2. Resilient Re-Link (every 30 seconds)
    # Re-Identify the Default Audio Device to fix 'exclusive mode' or hardware-sleep issues.
    if ($counter % 30 -eq 0) {
        try {
            $recognition.SetInputToDefaultAudioDevice()
            # Write-Host "DEBUG: Re-bound to default audio device."
        } catch {}
    }
}
