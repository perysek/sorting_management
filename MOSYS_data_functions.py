import pandas as pd
import pyodbc
from contextlib import contextmanager
from datetime import datetime

# Centralize the connection string
CONNECTION_STRING = (
	"DSN=STAAMP_DB;ArrayFetchOn=1;ArrayBufferSize=8;TransportHint=TCP;DecimalSymbol=,;;")


@contextmanager
def pervasive_connection(readonly: bool = True):
	"""A context manager for handling database connections."""
	conn_str = f"{CONNECTION_STRING}readonly={'True' if readonly else 'False'};"
	conn = None
	try:
		conn = pyodbc.connect(conn_str)
		yield conn
	except pyodbc.Error as e:
		print(f"Database connection error: {e}")
		raise
	finally:
		if conn:
			conn.close()


def get_pervasive(query: str, params: tuple = None) -> pd.DataFrame:
	"""Executes a read-only query and returns a cleaned pandas DataFrame."""
	with pervasive_connection(readonly=True) as conn:
		df = pd.read_sql(query, conn, params=params)
	
	# More efficient whitespace stripping
	for col in df.select_dtypes(include=['object']).columns:
		df[col] = df[col].str.strip()
	
	return df


def parse_mosys_date(date_value):
	"""Parse MOSYS date (YYYYMMDD format) to Python date object."""
	if date_value is None:
		return None
	if isinstance(date_value, str):
		date_str = date_value.strip()
		if len(date_str) == 8 and date_str.isdigit():
			# YYYYMMDD format
			try:
				return datetime.strptime(date_str, '%Y%m%d').date()
			except:
				return None
		elif '-' in date_str:
			# YYYY-MM-DD format
			try:
				return datetime.strptime(date_str, '%Y-%m-%d').date()
			except:
				return None
	return None


def get_niezgodnosc_details(nr_niezgodnosci: str) -> dict:
	"""
	Get data_niezgodnosci and nr_zamowienia for a single nr_niezgodnosci.
	Returns: {'data_niezgodnosci': date or None, 'nr_zamowienia': str or None}
	"""
	if not nr_niezgodnosci:
		return {'data_niezgodnosci': None, 'nr_zamowienia': None}
	
	query = '''
		SELECT NOTCOJAN.DATA, NOTCOJAN.COMMESSA
		FROM STAAMPDB.NOTCOJAN NOTCOJAN
		WHERE NOTCOJAN.NUMERO_NC = ?
	'''
	try:
		df = get_pervasive(query, (nr_niezgodnosci,))
		if not df.empty:
			data = parse_mosys_date(df.iloc[0]['DATA'])
			return {
				'data_niezgodnosci': data,
				'nr_zamowienia': df.iloc[0]['COMMESSA']
			}
	except Exception as e:
		print(f"Error fetching niezgodnosc details for {nr_niezgodnosci}: {e}")
	
	return {'data_niezgodnosci': None, 'nr_zamowienia': None}


def get_part_number(nr_zamowienia: str) -> str:
	"""
	Get kod_detalu (part number) for a given production order.
	Returns: part_number string or None
	"""
	if not nr_zamowienia:
		return None
	
	query = '''
		SELECT COLLAUDO.ARTICOLO
		FROM STAAMPDB.COLLAUDO COLLAUDO
		WHERE COLLAUDO.COMMESSA = ?
	'''
	try:
		df = get_pervasive(query, (nr_zamowienia,))
		if not df.empty:
			return df.iloc[0]['ARTICOLO']
	except Exception as e:
		print(f"Error fetching part number for {nr_zamowienia}: {e}")
	
	return None


def get_batch_niezgodnosc_details(nr_niezgodnosci_list: list) -> dict:
	"""
	Batch fetch data for multiple nr_niezgodnosci values.
	Returns: {nr_niezgodnosci: {'data_niezgodnosci': date, 'nr_zamowienia': str, 'kod_detalu': str}}
	"""
	if not nr_niezgodnosci_list:
		return {}
	
	# Filter out empty/None values
	nr_list = [nr for nr in nr_niezgodnosci_list if nr]
	if not nr_list:
		return {}
	
	result = {}
	
	# First query: get DATA and COMMESSA for all nr_niezgodnosci
	placeholders = ','.join(['?' for _ in nr_list])
	query = f'''
		SELECT NOTCOJAN.NUMERO_NC, NOTCOJAN.DATA, NOTCOJAN.COMMESSA
		FROM STAAMPDB.NOTCOJAN NOTCOJAN
		WHERE NOTCOJAN.NUMERO_NC IN ({placeholders})
	'''
	
	try:
		df = get_pervasive(query, tuple(nr_list))
		
		# Build intermediate results
		commessa_to_fetch = set()
		for _, row in df.iterrows():
			nr = row['NUMERO_NC']
			result[nr] = {
				'data_niezgodnosci': parse_mosys_date(row['DATA']),
				'nr_zamowienia': row['COMMESSA'],
				'kod_detalu': None
			}
			if row['COMMESSA']:
				commessa_to_fetch.add(row['COMMESSA'])
		
		# Second query: get ARTICOLO for all COMMESSA values
		if commessa_to_fetch:
			placeholders = ','.join(['?' for _ in commessa_to_fetch])
			query = f'''
				SELECT COLLAUDO.COMMESSA, COLLAUDO.ARTICOLO
				FROM STAAMPDB.COLLAUDO COLLAUDO
				WHERE COLLAUDO.COMMESSA IN ({placeholders})
			'''
			df_parts = get_pervasive(query, tuple(commessa_to_fetch))
			
			# Map COMMESSA to ARTICOLO
			commessa_to_articolo = dict(zip(df_parts['COMMESSA'], df_parts['ARTICOLO']))
			
			# Update results with kod_detalu
			for nr, data in result.items():
				if data['nr_zamowienia'] in commessa_to_articolo:
					data['kod_detalu'] = commessa_to_articolo[data['nr_zamowienia']]
	
	except Exception as e:
		print(f"Error in batch fetch: {e}")
	
	return result