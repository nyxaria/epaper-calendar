fireup()
{  
	sudo echo "hi"
	while true; do
		currenttime=$(date +%H:%M)
		if [[ "$currenttime" > "00:59" ]] && [[ "$currenttime" < "07:30" ]]; then
			echo "nightime, sleeping" && sleep 1200
		else
			cd ~/epaper-calendar && git pull && cd - && python3 ~/epaper-calendar/beautiful_calendar.py
		fi
                echo "restart router"
                sudo ifconfig wlan0 down
                sleep 20
                sudo ifconfig wlan0 up
		sleep 900
	done
}
