#include <Wire.h>
#include <TinyGPS++.h>
#include <Adafruit_Sensor.h>
#include <QMC5883LCompass.h>


QMC5883LCompass compass;



// Motor Driver Pins
#define motor1A 2
#define motor1B 3
#define motor2A 4
#define motor2B 5
#define motor3A 6
#define motor3B 7
#define motor4A 8
#define motor4B 9

// Ultrasonic Sensor Pins
#define trigPin 10
#define echoPin 11

// PIR Sensor Pin
#define pirPin 12

// TinyGPS++ object
TinyGPSPlus gps;

// Constants
#define obstacleThreshold 20
#define speed 150
#define targetDistance 10  // Distance to target in meters

// Array of target GPS coordinates (replace with your values)
float targets[][2] = {
  {12.780629, 75.184262},
  {12.780642, 75.184876},
  {12.780629, 75.184262},
  {12.780642, 75.184876}
};

int currentTarget = 0;

// Desired heading for orientation (in degrees)
float desiredHeading = 0;
void setup() {
  Serial.begin(9600); // Initialize serial communication for debugging

  compass.init();

  // Motor pins as output
  pinMode(motor1A, OUTPUT);
  pinMode(motor1B, OUTPUT);
  pinMode(motor2A, OUTPUT);
  pinMode(motor2B, OUTPUT);
  pinMode(motor3A, OUTPUT);
  pinMode(motor3B, OUTPUT);
  pinMode(motor4A, OUTPUT);
  pinMode(motor4B, OUTPUT);

  // Ultrasonic sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // PIR sensor pin
  pinMode(pirPin, INPUT);


}

void moveForward() {

  Serial.println("moveforward");
  digitalWrite(motor1A, HIGH);
  digitalWrite(motor1B, LOW);
  digitalWrite(motor2A, HIGH);
  digitalWrite(motor2B, LOW);
  digitalWrite(motor3A, HIGH);
  digitalWrite(motor3B, LOW);
  digitalWrite(motor4A, HIGH);
  digitalWrite(motor4B, LOW);
}

void stopMotors() {
  Serial.println("stopmotor");
  digitalWrite(motor1A, LOW);
  digitalWrite(motor1B, LOW);
  digitalWrite(motor2A, LOW);
  digitalWrite(motor2B, LOW);
  digitalWrite(motor3A, LOW);
  digitalWrite(motor3B, LOW);
  digitalWrite(motor4A, LOW);
  digitalWrite(motor4B, LOW);
}

void avoidObstacle() {
  Serial.println("avoidobstacles");
  // Perform obstacle avoidance here
  // For example, stop motors, turn away from the obstacle, then resume moving forward
  stopMotors();
  delay(500);
  // Turn right (you might need to adjust this based on your robot's design)
  digitalWrite(motor1A, LOW);
  digitalWrite(motor1B, HIGH);
  digitalWrite(motor2A, HIGH);
  digitalWrite(motor2B, LOW);
  digitalWrite(motor3A, LOW);
  digitalWrite(motor3B, HIGH);
  digitalWrite(motor4A, HIGH);
  digitalWrite(motor4B, LOW);
  delay(3000);
  // Resume forward movement
  moveForward();
  delay(3000);
}

float calculateBearing(float lat1, float lon1, float lat2, float lon2) {
  float dLon = lon2 - lon1;
  float y = sin(dLon) * cos(lat2);
  float x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dLon);
  float brng = atan2(y, x);
  brng = degrees(brng);
  brng = fmod((brng + 360), 360);
  return brng;
}


void adjustOrientation(float& currentHeading, int& x, int& y, int& z) {
  // Calculate the heading angle between the current location and the target destination
  float targetHeading = calculateBearing(gps.location.lat(), gps.location.lng(), targets[currentTarget][0], targets[currentTarget][1]);

  // Adjust the desiredHeading to match the calculated targetHeading
  desiredHeading = targetHeading;

  // Define the minimum rotation angle for adjustments
  float minRotationAngle = 5; // Adjust this value as needed

  // While heading error is not within acceptable range for adjustment
  while (true) {
    Serial.println(targetHeading);
    Serial.println(currentHeading);
    
    

    float headingError = desiredHeading - currentHeading;

    // Normalize heading error to be between -180 and 180 degrees
    if (headingError > 180) {
      headingError -= 360;
    } else if (headingError < -180) {
      headingError += 360;
    }

    // Exit the loop if heading error is small enough
    if (abs(headingError) < minRotationAngle) {
      break;
    }

    // Determine the direction of rotation
    int rotationDirection =  1;

    // Set the motor control pins for rotation
    if (rotationDirection == 1) {
      // Turn right
      digitalWrite(motor1A, HIGH);
      digitalWrite(motor1B, LOW);
      digitalWrite(motor2A, LOW);
      digitalWrite(motor2B, HIGH);
      digitalWrite(motor3A, HIGH);
      digitalWrite(motor3B, LOW);
      digitalWrite(motor4A, LOW);
      digitalWrite(motor4B, HIGH);
    } else {
      // Turn left
      digitalWrite(motor1A, LOW);
      digitalWrite(motor1B, HIGH);
      digitalWrite(motor2A, HIGH);
      digitalWrite(motor2B, LOW);
      digitalWrite(motor3A, LOW);
      digitalWrite(motor3B, HIGH);
      digitalWrite(motor4A, HIGH);
      digitalWrite(motor4B, LOW);
    }

    // Wait for a short duration to allow the robot to adjust its orientation
    delay(100);

    // Stop the rotation
    stopMotors();

    // Update the current heading
    compass.read();
    x = compass.getX();
    y = compass.getY();
    z = compass.getZ();
    currentHeading = atan2(y, x) * 180.0 / M_PI;
    if (currentHeading < 0) {
      currentHeading += 360.0;
    }
  }
}



void loop() {
  // Read GPS data
  if (Serial.available() > 0) {
  if (gps.encode(Serial.read())) {
      if (gps.location.isValid()) {
    
        // Read GPS data when available
        int x, y, z;
        float currentLat = gps.location.lat();

        
        float currentLon = gps.location.lng();

        

        float distance = TinyGPSPlus::distanceBetween(currentLat, currentLon, targets[currentTarget][0], targets[currentTarget][1]);

        // Read magnetometer data for current heading
       // Read compass values
  compass.read();

  // Return XYZ readings
  x = compass.getX();
  y = compass.getY();
  z = compass.getZ();

  float currentHeading = atan2(y, x) * 180.0 / M_PI;
  if (currentHeading < 0) {
    currentHeading += 360.0;
  }
  
        // Adjust robot's orientation
        adjustOrientation(currentHeading, x,y,z);

        // Check for obstacles
        long duration, distanceFront;

        // Trigger ultrasonic sensor
        digitalWrite(trigPin, LOW);
        delayMicroseconds(2);
        digitalWrite(trigPin, HIGH);
        delayMicroseconds(10);
        digitalWrite(trigPin, LOW);

        // Measure the echo duration
        duration = pulseIn(echoPin, HIGH);

        // Calculate distance in cm
        distanceFront = (duration / 2) / 29.1;

        // Check for obstacles in front
        if (digitalRead(pirPin) == HIGH && distanceFront < obstacleThreshold) {
          // Obstacle detected, avoid it
          //Serial.println("avoid");
          avoidObstacle();
          delay(100);
        } else if (distance < targetDistance) {
          // Target reached, stop the robot
          stopMotors();
          // Move to the next target
          currentTarget = (currentTarget + 1) % (sizeof(targets) / sizeof(targets[0]));
          delay(2000); // Wait for 2 seconds before moving to the next target
        } else {
          // No obstacle, move forward
          //Serial.println("forward");
          moveForward();
        }


      }

      else {
        delay(1000);
      }
    }
  }
}
