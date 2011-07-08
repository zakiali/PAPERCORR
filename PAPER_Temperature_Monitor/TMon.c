// Author: J. Aguirre
// Last revised 2010/05/15
// Based on LabJack example software for the "easy" functions, rev Oct. 8, 2007

#include "ue9.h"
#include <time.h>

#define NTHERMS 4
const int ue9_port = 52360;

int readIntTemp(int socketFD, 
		ue9CalibrationInfo *caliInfo, double *dblIntTemp);

int main(int argc, char **argv)
{
  int socketFD, i, j;
  ue9CalibrationInfo caliInfo;
  long error;
  double dblVoltage, dblIntTemp, TKelvin[NTHERMS];
  long alngEnableTimers[6], alngTimerModes[6], alngEnableCounters[2], 
    alngReadTimers[6];
  long alngUpdateResetTimers[6], alngReadCounters[2], alngResetCounters[2];
  double adblTimerValues[6], adblCounterValues[2];

  char datafile[80];
  
  int                hour, lasthour;
  time_t             timep;
  struct tm          tm;
  FILE *data_fd, *tnow_fd, *cal_fd;

  double cal_coeffs[2][NTHERMS];  

/* Calibration coefficients were determined from the night of
   2005/05/15, calibrating using the HOBO */

//       26.011521      0.89395315
//       3.8793608      0.96553796
//       21.189119      0.89810403
//       24.789991      0.89390865

// There *must* be a better way to do this
  cal_coeffs[0][3] = 26.011521;
  cal_coeffs[1][3] = 0.89395315;
  cal_coeffs[0][2] = 3.8793608;
  cal_coeffs[1][2] = 0.96553796;
  cal_coeffs[0][1] = 21.189119;
  cal_coeffs[1][1] = 0.89810403;
  cal_coeffs[0][0] = 24.789991;
  cal_coeffs[1][0] = 0.89390865;

  cal_fd = fopen("ThermometerCalibrationConstants.txt", "w");
  for (j=0; j<4; j++) {
    for (i=0; i<2; i++) {
      fprintf(cal_fd,"%12.8f ",
	      cal_coeffs[i][j]);
    }
    fprintf(cal_fd,"\n");
  }
  fprintf(cal_fd,"\n");
  fflush(cal_fd);
  fclose(cal_fd);

  // Ugh.  Can't remember how to do this.
//  cal_fd = fopen("ThermometerCalibrationConstants.txt", "r");
//  for (j=0; j<4; j++) {
//    for (i=0; i<2; i++) {
//      cal_coeffs[i][j] = fscanf(cal_fd,"%12f ");
//      printf("%12.8f ",cal_coeffs[i][j]);
//    }
//    printf("\n");
//  }
//  fclose(cal_fd);
//

  for(i = 0; i < 6; i++)
  {
    alngEnableTimers[i] = 0;
    alngTimerModes[i] = 0;
    adblTimerValues[i] = 0.0;
    alngReadTimers[i] = 0;
    alngUpdateResetTimers[i] = 0;
    if(i < 2)
    {
      alngEnableCounters[i] = 0;
      alngReadCounters[i] = 0;
      alngResetCounters[i] = 0;
      adblCounterValues[i] = 0.0;
    }
  }
  
  if(argc < 2)
  {
    printf("Please enter an ip address to connect to.\n");
    exit(0);
  }
  else if(argc > 2)
  {
    printf("Too many arguments.\nPlease enter only an ip address.\n");
    exit(0);
  }

  //Opening TCP connection to UE9
  printf("Opening TCP connection to %s\n",argv[1]);
  if( (socketFD = openTCPConnection(argv[1], ue9_port)) < 0)
    goto done;

  //Getting calibration information from UE9
  printf("Getting calibration information.\n");
  if(getCalibrationInfo(socketFD, &caliInfo) < 0)
    goto close;

  //Disable all timers and counters
  for(i = 0; i < 6; i++)
    alngEnableTimers[i] = 0;
  alngEnableCounters[0] = 0;
  alngEnableCounters[1] = 0;
  if((error = eTCConfig(socketFD, alngEnableTimers, alngEnableCounters, 
			0, 0, 0, alngTimerModes, adblTimerValues, 0, 0)) != 0)
    goto close;
  printf("Calling eTCConfig to disable all timers and counters\n");

  time(&timep);
  tm = *localtime(&timep);
  // There is a way to get UT time ...
  //  tm = *uttime(&timep);
  hour = tm.tm_hour;
  lasthour = hour;

  sprintf(datafile,"%04i%02i%02i_%02i%02i.txt",
	  tm.tm_year+1900,tm.tm_mon+1,tm.tm_mday,tm.tm_hour,tm.tm_min);

  data_fd = fopen(datafile, "w");

  printf("\nBegin acquiring data.\n");
  printf("Type ctrl-C to quit.\n");

  while(1) {

    time(&timep);
    tm = *localtime(&timep);
    hour = tm.tm_hour;
    
    if (hour != lasthour){
      fclose(data_fd);
      sprintf(datafile,"%04i%02i%02i_%02i00.txt",
	  tm.tm_year+1900,tm.tm_mon+1,tm.tm_mday,tm.tm_hour);
      data_fd = fopen(datafile, "w");
    }

    fprintf(data_fd,"%04i/%02i/%02i  %02i:%02i:%02i   ",
	   tm.tm_year+1900,tm.tm_mon+1,tm.tm_mday, 
	   tm.tm_hour, tm.tm_min, tm.tm_sec);

    dblIntTemp = 0;
    if(readIntTemp(socketFD, &caliInfo, &dblIntTemp) < 0)
      goto close;
    fprintf(data_fd,"%.3f  ",dblIntTemp);

    // Read the voltage from AIN0-3 using 0-5 volt range at 16 bit resolution
    for (i=0; i<NTHERMS; i++)
      {
        if((error = eAIN(socketFD, &caliInfo, i, 0, &dblVoltage, LJ_rgUNI5V, 
			 16, 0, 0, 0, 0)) != 0)
          goto close;
	TKelvin[i] = (dblVoltage * 100) * 
	  cal_coeffs[1][i] + cal_coeffs[0][i];
      }

    // Print data out to file
    for (i=0; i<NTHERMS; i++)
      {
	fprintf(data_fd,"%10.3f   ", TKelvin[i]);
      }
    fprintf(data_fd,"\n");
    fflush(data_fd);

    tnow_fd = fopen("TNow","w");

    for (i=0; i<NTHERMS; i++)
      {
	fprintf(tnow_fd,"%10.3f   ", TKelvin[i]);
      }
    fprintf(tnow_fd,"\n");
    fflush(tnow_fd);
    fclose(tnow_fd);

	sleep(1);
//    usleep(1000);
    
    lasthour = hour;
  }

close:
  if(error > 0)
    printf("Received an error code of %ld\n", error);
  if(closeTCPConnection(socketFD) < 0)
  {
    printf("Error: failed to close socket\n");
    return 1;
  }
done:
  return 0;
}

int readIntTemp(int socketFD, ue9CalibrationInfo *caliInfo, 
		double *dblIntTemp)
{
  uint8 sendBuff[8], recBuff[8];
  int sendChars, recChars;
  //  double voltage;
  double temperature; //in Kelvins
  uint16 bytesTemperature;
  uint8 ainResolution;

  ainResolution = 12;

  /* read temperature from internal temperature sensor */
  sendBuff[1] = (uint8)(0xA3);  //command byte
  sendBuff[2] = (uint8)(0x04);  //IOType = 4 (analog in)
  sendBuff[3] = (uint8)(0x85);  //Channel = 133 (tempSensor)
  sendBuff[4] = (uint8)(0x00);  //Gain = 1 (Bip does not apply)  
  sendBuff[5] = (uint8)(0x0C);  //Resolution = 12
  sendBuff[6] = (uint8)(0x00);  //SettlingTime = 0
  sendBuff[7] = (uint8)(0x00);  //Reserved
  sendBuff[0] = normalChecksum8(sendBuff, 8);

  //Sending command to UE9
  sendChars = send(socketFD, sendBuff, 8, 0);
  if(sendChars < 8)
  {
    if(sendChars == -1)
      goto sendError0;
    else  
      goto sendError1;
  }

  //Receiving response from UE9
  recChars = recv(socketFD, recBuff, 8, 0);
  if(recChars < 8)
  {
    if(recChars == -1)
      goto recvError0;
    else  
      goto recvError1;
  }

  if((uint8)(normalChecksum8(recBuff, 8)) != recBuff[0])
    goto chksumError;

  if(recBuff[1] != (uint8)(0xA3))
    goto commandByteError;

  if(recBuff[2] != (uint8)(0x04))
    goto IOTypeError;

  if(recBuff[3] != (uint8)(0x85))
    goto channelError;

  bytesTemperature = recBuff[5] + recBuff[6] * 256;

  //assuming high power level
  if(binaryToCalibratedAnalogTemperature(caliInfo, 0, bytesTemperature, 
					 &temperature) < 0)
    return -1;

  *dblIntTemp = temperature;
  
  return 0;

//error printouts
sendError0:
  printf("Error : send failed\n");
  return -1;
sendError1:
  printf("Error : did not send all of the buffer\n");
  return -1;
recvError0:
  printf("Error : recv failed\n");
  return -1;
recvError1:  
  printf("Error : recv did not receive all of the buffer\n");
  return -1;
chksumError:
  printf("Error : received buffer has bad checksum\n");
  return -1;
commandByteError:
  printf("Error : received buffer has wrong command byte\n");
  return -1;
IOTypeError:  
  printf("Error : received buffer has wrong IOType\n");
  return -1;
channelError:  
  printf("Error : received buffer has wrong channel\n");
  return -1;

}


