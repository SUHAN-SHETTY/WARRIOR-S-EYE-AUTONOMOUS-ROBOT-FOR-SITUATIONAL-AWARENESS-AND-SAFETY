import os
import cv2
import numpy as np
from imutils import paths
import pickle
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
from keras.preprocessing.image import ImageDataGenerator
from keras.layers import Input, AveragePooling2D, Flatten, Dense, Dropout
from keras.models import Model
from keras.applications import ResNet50
from keras.optimizers import SGD
from keras import optimizers

datapath = r"D:\videoclassifier\data"
outputmodel = r"D:\videoclassifier\videoclassificationmodel\classificationmodel"
outputlabelbinarize = r"D:\videoclassifier\videoclassificationmodel\classificationbinarizer"
epoch = 25

warlabels = set(['bombblast', 'firing', 'tank'])
print("Images are being loaded ...")
pathtoimages = list(paths.list_images(datapath))
data = []
labels = []

for image_path in pathtoimages:
    label = image_path.split(os.path.sep)[-2]
    if label not in warlabels:
        continue
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (224, 224))
    data.append(image)
    labels.append(label)

data = np.array(data)
labels = np.array(labels)

# One-hot encoded values as 0, 1, 2
lb = LabelBinarizer()
labels = lb.fit_transform(labels)

# Convert data to float32
data = data.astype("float32")

(X_train, X_test, Y_train, Y_test) = train_test_split(data, labels, test_size=0.25, stratify=labels, random_state=42)

trainingAugmentation = ImageDataGenerator(
    rotation_range=30,
    zoom_range=0.15,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.15,
    horizontal_flip=True,
    fill_mode="nearest"
)

validationAugmentation = ImageDataGenerator()

mean = np.array([123.68, 116.779, 103.939], dtype="float32")
trainingAugmentation.mean = mean
validationAugmentation.mean = mean

# Define the model
input_tensor = Input(shape=(224, 224, 3))
weights_path = r"C:\Users\SUHAN\.keras\models\resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5"
baseModel = ResNet50(weights=weights_path, include_top=False, input_tensor=input_tensor)

headModel = baseModel.output
headModel = AveragePooling2D(pool_size=(7, 7))(headModel)
headModel = Flatten(name="flatten")(headModel)
headModel = Dense(512, activation="relu")(headModel)
headModel = Dropout(0.5)(headModel)
headModel = Dense(len(lb.classes_), activation="softmax")(headModel)

model = Model(inputs=baseModel.input, outputs=headModel)

# Freeze the layers of the base model
for basemodelLayers in baseModel.layers:
    basemodelLayers.trainable = False

# Use the learning rate scheduler with decay
lr_schedule = optimizers.schedules.ExponentialDecay(initial_learning_rate=0.0001,
                                                    decay_steps=100000,
                                                    decay_rate=0.96)

opt = SGD(learning_rate=lr_schedule, momentum=0.9)

model.compile(loss="categorical_crossentropy", optimizer=opt, metrics=["accuracy"])

# Train the model
History = model.fit_generator(
    trainingAugmentation.flow(X_train, Y_train, batch_size=32),
    steps_per_epoch=len(X_train) // 32,
    validation_data=validationAugmentation.flow(X_test, Y_test),
    validation_steps=len(X_test) // 32,
    epochs=epoch
)

# Save the model
model.save(outputmodel)

# Save the label binarizer
binarizer_filepath = os.path.join(outputlabelbinarize, 'videoclassification_binarizer.pickle')
os.makedirs(os.path.dirname(binarizer_filepath), exist_ok=True)  # Create directory if it doesn't exist

with open(binarizer_filepath, 'wb') as binarizer_file:
    binarizer_file.write(pickle.dumps(lb))
