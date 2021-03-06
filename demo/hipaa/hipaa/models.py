from django.db.models import Model, ManyToManyField, ForeignKey, OneToOneField, CharField, TextField, DateField, DateTimeField, IntegerField, FileField, BooleanField

from jeevesdb.JeevesModel import JeevesModel as Model
from django.contrib.auth.models import User
from jeevesdb.JeevesModel import JeevesForeignKey as ForeignKey
from jeevesdb.JeevesModel import label_for

from sourcetrans.macro_module import macros, jeeves
import JeevesLib

from settings import CONF_PHASE as phase

class Address(Model):
	"""
	Mailing address of a person's residency.
	"""
	Street=CharField(max_length=100, blank=True, null = True, help_text="Number and name of street")
	City=CharField(max_length=30, help_text="Name of City")
	State=CharField(max_length=20, help_text="Two-letter abbreviation for state")
	ZipCode=CharField(max_length=5, help_text="Zip Code")
	def String(self):
		"""
		Returns a string representation of this address.
		"""
		return self.Street+"\n"+self.ZipCode+" "+self.City+", "+self.State
	class Meta:
		db_table = 'Address'
	@staticmethod
	def jeeves_get_private_Street(user):
		return ""
	@staticmethod
	@label_for('Street')
	@jeeves
	def jeeves_restrict_Addresslabel(address, ctxt):
		return False

class Individual(Model):
	"""
	A single person who can be a patient to a covered entity,
	and might have any/all other attributes of people.
	"""
	FirstName = CharField(max_length=1024, help_text="First name of patient")
	Email = CharField(max_length=1024, blank=True, null = True, help_text="Email of individual")
	Address = ForeignKey(Address, blank=True, null = True, help_text="Home address of patient, references an Address object.")
	BirthDate = DateField(blank=True, null = True, help_text="Date of birth of patient")
	Sex = CharField(max_length=6, blank=True, null = True, help_text="Birth sex of patient")
	#Parent = ForeignKey("self",blank=True,null=True, help_text="Other individual with legal parental status")
	LastName = CharField(max_length=1024, help_text="Last name of patient")
	UID = IntegerField(primary_key=True, help_text="Auto-incrementing primary key")
	SSN = CharField(max_length=9, blank=True, null = True, help_text="Government given SSN of patient")
	TelephoneNumber = CharField(max_length=10, blank=True, null = True, help_text="Phone number to reach patient")
	DriversLicenseNumber = CharField(max_length=20, blank=True, null = True, help_text="Driver's licence number of patient")
	Employer = CharField(max_length=50, blank=True, null = True, help_text="Company that employs patient")
	FaxNumber = CharField(max_length=10, blank=True, null = True, help_text="Fax number to reach patient")
	#PersonalRepresentative = ForeignKey("self",blank=True,null=True, help_text="Other indivual with legal right to make medical decisions for individual.")
	ReligiousAffiliation = CharField(max_length=100, blank=True, null = True, help_text="Self-described religious affiliation")
	class Meta:
		db_table = 'Individual'
	def Name(self):
		return self.FirstName +" "+self.LastName
	@staticmethod
	def jeeves_get_private_SSN(individual):
		return ""
	@staticmethod
	def jeeves_get_private_TelephoneNumber(individual):
		return ""
	@staticmethod
	def jeeves_get_private_DriversLicenseNumber(individual):
		return ""
	@staticmethod
	@label_for('SSN')
	@label_for('TelephoneNumber')
	@label_for('DriversLicenseNumber')
	@jeeves
	def jeeves_restrict_Individuallabel(individual, ctxt):
		return ctxt.individual==individual

class BusinessAssociate(Model):
	"""
	Persons or corporations that perform services for covered entities. They may
	or may not be covered entities themselves.
	"""
	Name = CharField(max_length=1024, help_text="Business name of business associate")
	#CoveredIdentity = ForeignKey("CoveredEntity", null=True, blank=True, help_text="Covered Entity object representing the same entity as this business associate")
	Covered = BooleanField(help_text="If the business associate is a covered entity") #Because the above line doesn't work yet in Jeeves (circular references)
	class Meta:
		db_table = 'BusinessAssociate'

class CoveredEntity(Model):
	"""
	Health plan, health clearinghouse,
	or health care provider making sensitive transactions. This includes hospitals.
	"""
	EIN = CharField(max_length=9, blank=False, null=False,unique=True, help_text="Government issued Employer Identification Number, should be uniquely identifiable")
	Name = CharField(max_length=1024, help_text="Entity's name")
	Directory = ManyToManyField(Individual,through="HospitalVisit", help_text="Patients currently checked in to entity")
	Associates = ManyToManyField(BusinessAssociate,through="BusinessAssociateAgreement", help_text="Business Associates that the entity uses.")
	class Meta:
		db_table = 'CoveredEntity'

class HospitalVisit(Model):
	"""
	Patient's visit to a hospital for medical purposes
	"""
	Patient = ForeignKey(Individual, help_text="Patient visiting")
	Hospital = ForeignKey(CoveredEntity, related_name="Patients", help_text="Hospital visited")
	DateAdmitted = DateField(help_text="Date patient checked in to hospital")
	Location = TextField(blank=True, null = True, help_text="Current location of patient within entity's grounds")
	Condition = TextField(blank=True, null = True, help_text="Vague description of patient's condition")
	DateReleased = DateField(blank=True, null=True, help_text="Date patient checked out of hospital. Blank if patient still in hospital")
	class Meta:
		db_table = 'HospitalVisit'
	@label_for('Location')
	@jeeves
	def jeeves_restrict_HospitalVisitlabel(visit, ctxt):
		if ctxt.type==1:
			return visit.Patient==ctxt.individual
		elif ctxt.type==2:
			return visit.Hospital==ctxt.entity
		elif ctxt.type==6:
			return True
	@staticmethod
	def jeeves_get_private_Patient(individual):
		return ""
	@staticmethod
	def jeeves_get_private_Location(individual):
		return ""

class Treatment(Model):
	"""
	Provided medical treatment, medication, or service.
	"""
	Service = CharField(max_length=100, help_text="Code for medical service provided")
	DatePerformed = DateField(help_text="Date on which the service was performed")
	PrescribingEntity = ForeignKey(CoveredEntity, related_name="Prescriptions", help_text="Entity that prescribed this service")
	PerformingEntity = ForeignKey(CoveredEntity, help_text="Entity that performed this service")
	Patient = ForeignKey(Individual, help_text="Patient whom received this service")
	class Meta:
		db_table = 'Treatment'
	@label_for('Patient')
	@jeeves
	def jeeves_restrict_Treatmentlabel(treatment, ctxt):
		if ctxt.type==1:
			return treatment.Patient==ctxt.individual or treatment.Patient.personalRepresentative_set.get(ctxt.individual.user).length>0
		elif ctxt.type==2:
			return treatment.PrescribingEntity==ctxt.entity or treatment.PrescribingEntity==ctxt.entity
	@staticmethod
	def jeeves_get_private_Patient(individual):
		return Individual(LastName="Anonymous", UID=)

class Diagnosis(Model): 
	""""
	Recognition of health condition or situation by a medical professional.
	"""
	Manifestation = CharField(max_length=100, help_text="Code")
	Diagnosis = CharField(max_length=255, help_text="The details of how the disease has manifested.")
	DateRecognized = DateField(help_text="Date the diagnosis was made")
	RecognizingEntity = ForeignKey(CoveredEntity, help_text="Entity that made the diagnosis")
	Patient = ForeignKey(Individual, help_text="Person to whom the diagnosis applies")
	class Meta:
		db_table = 'Diagnosis'
	@label_for('Patient')
	@jeeves
	def jeeves_restrict_Diagnosislabel(diagnosis, ctxt):
		if ctxt.type==1:
			return diagnosis.Patient==ctxt.individual
		elif ctxt.type==2:
			return diagnosis.RecognizingEntity==ctxt.entity
	@staticmethod
	def jeeves_get_private_Patient(individual):
		return None

class InformationTransferSet(Model):
	"""
	Collection of private information that can be shared
	"""
	class Meta:
		db_table = 'InformationTransferSet'

class TreatmentTransfer(Model):
	"""
	Datum about treatment offered and performed on patients
	"""
	Set = ForeignKey(InformationTransferSet, related_name="Treatments", help_text="Data set transferred")
	Treatment = ForeignKey(Treatment, help_text="Treatment in the dataset")
	class Meta:
		db_table = 'TreatmentTransfer'

class DiagnosisTransfer(Model):
	"""
	Datum about diagnoses made about patients
	"""
	Set = ForeignKey(InformationTransferSet, related_name="Diagnoses", help_text="Data set transferred")
	Diagnosis = ForeignKey(Diagnosis, help_text="Diagnosis in the dataset")
	class Meta:
		db_table = 'DiagnosisTransfer'

class HospitalVisitTransfer(Model):
	"""
	Datum about patient's visiting a hospital
	"""
	Set = ForeignKey(InformationTransferSet, related_name="Visits", help_text="Data set transferred")
	Visit = ForeignKey(HospitalVisit, help_text="Hospital visit in the dataset")
	class Meta:
		db_table = 'HospitalVisitTransfer'

class BusinessAssociateAgreement(Model):
	"""
	Agreement between a business associate and a covered entity where 
	the covered entity gives the business associate its data,
	and the business associate completes the entity's transactions by standard
	"""
	BusinessAssociate = ForeignKey(BusinessAssociate, related_name="Associations", help_text="Business Associate working for the entity")
	CoveredEntity = ForeignKey(CoveredEntity, related_name="Associations", help_text="Covered Entity hiring the business associate")
	SharedInformation = OneToOneField(InformationTransferSet, help_text="Information shared from covered entity to business associate")
	Purpose = TextField(blank=True, null = True, help_text="Purpose business associate serves for covered entity")
	class Meta:
		db_table = 'BusinessAssociateAgreement'
	@staticmethod
	def jeeves_get_private_SharedInformation(agreement):
		return None
	@staticmethod
	@label_for('SharedInformation')
	@jeeves
	def jeeves_restrict_BusinessAssociateAgreementlabel(agreement, profile):
		return agreement.CoveredEntity==profile.entity or agreement.BusinessAssociate==profile.associate

class Transaction(Model):
	"""
	A defined standard transaction between covered entitities.

	Attributes:
	Standard - Transaction Code: ICS-10-PCS, HCPCS, e.g.
	FirstParty, SecondParty - Covered entities performing the transaction
	SharedInformation - Information transferred between the parties to fulfill the transaction.
	"""

	Standard = CharField(max_length=100, help_text="Standard that the transaction abides by")
	FirstParty = ForeignKey(CoveredEntity, related_name = "SomeTransactions", help_text="First Covered Entity transferring data")
	SecondParty = ForeignKey(CoveredEntity, related_name = "MoreTransactions", help_text="Second Covered Entity transferring data")
	SharedInformation = OneToOneField(InformationTransferSet, help_text="Data shared from one entity to another")
	DateRequested = DateField(help_text="Date the data transfer was requested")
	DateResponded = DateField(help_text="Date the data transfer was responded to")
	Purpose = TextField(blank=True, null = True, help_text="Purpose for the data transfer")
	class Meta:
		db_table = 'Transaction'
	@label_for('Standard')
	@label_for('FirstParty')
	@label_for('SecondParty')
	@label_for('Purpose')
	@jeeves
	def jeeves_restrict_Transactionlabel(transaction, ctxt):
		if ctxt.type==2:
			return transaction.FirstParty==ctxt.entity or transactionn.SecondParty==ctxt.entity
		return False
	@staticmethod
	def jeeves_get_private_Standard(transaction):
		return ""
	@staticmethod
	def jeeves_get_private_Purpose(transaction):
		return ""
	@staticmethod
	def jeeves_get_private_FirstParty(transaction):
		return None
	@staticmethod
	def jeeves_get_private_SecondParty(transaction):
		return None

class PersonalRepresentative(Model):
	""""
	Relationship of a person who can make medical decisions for another.
	"""
	Dependent = ForeignKey(Individual, help_text = "Patient for whom decisions are made.")
	Representative = ForeignKey(Individual, related_name='Dependents', help_text ="Individual making decisions for another.")
	Parent = BooleanField(help_text ="If the representative has the right to be the representative because of a parental status.")
	class Meta:
		db_table = 'PersonalRepresentative'

class UserProfile(Model):
	""""
	Information about a user of the website.
	"""
	user = OneToOneField(User, help_text="User this information is about")
	email = CharField(max_length=1024, help_text="The user's email address")
	type = IntegerField(help_text="Type of body this user is about. 0=None, 1=Individual, 2=CoveredEntity, 3=BusinessAssociate, 4=Government, 5=Research, 6=Clergy")
	name = CharField(max_length=1024, help_text="The user's name. Not sure if this is ever needed")
	entity = ForeignKey(CoveredEntity, blank=True, null=True, help_text="The covered entity this user represents")
	associate = ForeignKey(BusinessAssociate, blank=True, null=True, help_text="The business associate this user represents")
	individual = ForeignKey(Individual, blank=True, null=True, help_text="The individual this user represents")
	@staticmethod
	def jeeves_get_private_email(user):
		return ""
	@staticmethod
	@label_for('email')
	@jeeves
	def jeeves_restrict_userprofilelabel(user, ctxt):
		return user == ctxt or (ctxt != None and ctxt.level == 'chair')
	class Meta:
		db_table = 'UserProfile'

class UserPCConflict(Model):
	user = ForeignKey(UserProfile, null=True, related_name='userpcconflict_user')
	pc = ForeignKey(UserProfile, null=True, related_name='userpcconflict_pc')
	
	@staticmethod
	def jeeves_get_private_user(uppc):
		return None
	@staticmethod
	def jeeves_get_private_pc(uppc):
		return None
	
	@staticmethod
	@label_for('user', 'pc')
	@jeeves
	def jeeves_restrict_userpcconflictlabel(uppc, ctxt):
		return True
		#return ctxt.level == 'chair' or uppc.user == ctxt
	class Meta:
		db_table = 'UserPCConflict'